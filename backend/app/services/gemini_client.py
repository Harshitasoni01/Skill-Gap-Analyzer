import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
RETRY_WAIT_SECONDS = 10

_client = None


class AIServiceError(Exception):
     def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise AIServiceError(
                "GEMINI_API_KEY is not set on the server. Add it to backend/.env and restart.",
                500,
            )
        _client = genai.Client(api_key=api_key)
    return _client


def call_gemini(prompt: str, max_retries: int = 3) -> str:
    client = _get_client()
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            text = (response.text or "").strip()
            if not text:
                raise AIServiceError("The AI returned an empty response. Please try again.")
            return text

        except AIServiceError:
            raise

        except Exception as e:
            error_text = str(e)
            is_rate_limit = "429" in error_text or "RESOURCE_EXHAUSTED" in error_text
            is_busy = "503" in error_text or "UNAVAILABLE" in error_text

            # A per-day quota will not reset in 10 seconds, so do not retry it.
            if is_rate_limit and "PerDay" in error_text:
                raise AIServiceError(
                    "The daily free quota for the Gemini API is used up. Try again tomorrow "
                    "or use a different API key.",
                    429,
                )

            if is_rate_limit or is_busy:
                last_error = e
                print(f"[Gemini] Temporary error, retry {attempt}/{max_retries} in {RETRY_WAIT_SECONDS}s")
                if attempt < max_retries:
                    time.sleep(RETRY_WAIT_SECONDS)
                continue

            print(f"[Gemini] Non-retryable error: {error_text}")
            raise AIServiceError("The AI request failed. Check the server log for details.")

    if last_error is not None and ("429" in str(last_error) or "RESOURCE_EXHAUSTED" in str(last_error)):
        raise AIServiceError("Gemini is rate-limiting requests right now. Wait a minute and try again.", 429)
    raise AIServiceError("The AI service is busy right now. Please try again in a moment.", 503)
