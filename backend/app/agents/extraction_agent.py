from app.services.gemini_client import AIServiceError, call_gemini
from app.services.utils import clean_list, clean_str, parse_json_object

MAX_RESUME_CHARS = 12000


def extract_candidate_info(resume_text: str) -> dict:
    """Agent 1: read the raw resume and return a structured profile."""
    prompt = f"""
You are a resume parsing assistant. Read the resume text below and extract information.

Return ONLY a valid JSON object with this exact structure, no extra text, no markdown formatting:

{{
  "name": "candidate full name or null",
  "email": "candidate email or null",
  "skills": ["skill1", "skill2"],
  "experience_years": "total years of experience as a string, e.g. '3 years' or null",
  "projects": ["short project description 1", "short project description 2"],
  "education": "highest education detail as a string or null",
  "companies": ["company1", "company2"]
}}

Resume text:
{resume_text[:MAX_RESUME_CHARS]}
"""

    raw_response = call_gemini(prompt)

    try:
        data = parse_json_object(raw_response)
    except ValueError:
        raise AIServiceError(
            "The AI returned an unreadable answer while reading the resume. Please try again."
        )

    return {
        "name": clean_str(data.get("name")),
        "email": clean_str(data.get("email")),
        "skills": clean_list(data.get("skills"), limit=40),
        "experience_years": clean_str(data.get("experience_years")),
        "projects": clean_list(data.get("projects"), limit=10),
        "education": clean_str(data.get("education")),
        "companies": clean_list(data.get("companies"), limit=10),
    }
