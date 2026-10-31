from app.agents.extraction_agent import extract_candidate_info
from app.agents.matching_agent import match_candidate_to_job


def verdict_for(score: int) -> str:
    if score >= 75:
        return "Strong match"
    if score >= 50:
        return "Partial match"
    return "Weak match"


def analyze_resume(resume_text: str, jd_text: str) -> dict:
    profile = extract_candidate_info(resume_text)
    match = match_candidate_to_job(jd_text, profile, resume_text)

    return {
        "candidate_name": profile["name"],
        "resume_skills": profile["skills"],
        "match_score": match["match_score"],
        "verdict": verdict_for(match["match_score"]),
        "matched_skills": match["matched_skills"],
        "missing_skills": match["missing_skills"],
        "reasons": match["reasons"],
    }
