from app.services.gemini_client import AIServiceError, call_gemini
from app.services.utils import clean_list, parse_json_object

MAX_JD_CHARS = 8000
MAX_RESUME_CHARS = 6000


def match_candidate_to_job(job_description: str, profile: dict, resume_text: str) -> dict:
    """Agent 2: compare the candidate with the job and find matched / missing skills.
    """
    prompt = f"""
You are an expert technical recruiter. Compare this candidate with the job description
and give an honest skill-gap assessment.

Job Description:
{job_description[:MAX_JD_CHARS]}

Candidate profile (structured):
Skills: {profile.get("skills")}
Experience: {profile.get("experience_years")}
Projects: {profile.get("projects")}
Education: {profile.get("education")}
Companies: {profile.get("companies")}

Full resume text (read it to judge the depth and quality of the candidate's work, not just keywords):
{resume_text[:MAX_RESUME_CHARS]}

Instructions:
1. Work out the key skills, tools and requirements the job description asks for.
2. matched_skills: required skills the candidate clearly has (evidence in the profile or resume).
3. missing_skills: required skills the candidate does not show.
4. match_score: an integer from 0 to 100 for overall fit. Judge real depth of work, not keyword overlap.
   Be honest and critical, not generous.
5. reasons: exactly 3 short, specific sentences that explain the score.
6. Use at most 15 skills in each list and use the job description's own wording for skill names.

Return ONLY a valid JSON object with this exact structure, no extra text, no markdown formatting:

{{
  "match_score": 72,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "reasons": ["reason 1", "reason 2", "reason 3"]
}}
"""

    raw_response = call_gemini(prompt)

    try:
        data = parse_json_object(raw_response)
    except ValueError:
        raise AIServiceError(
            "The AI returned an unreadable answer while matching. Please try again."
        )

    try:
        score = int(round(float(data.get("match_score", 0))))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))

    return {
        "match_score": score,
        "matched_skills": clean_list(data.get("matched_skills"), limit=15),
        "missing_skills": clean_list(data.get("missing_skills"), limit=15),
        "reasons": clean_list(data.get("reasons"), limit=5),
    }
