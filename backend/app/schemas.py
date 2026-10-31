from typing import List, Optional

from pydantic import BaseModel


class AnalysisResponse(BaseModel):
    candidate_name: Optional[str] = None
    resume_skills: List[str]
    match_score: int
    verdict: str
    matched_skills: List[str]
    missing_skills: List[str]
    reasons: List[str]
