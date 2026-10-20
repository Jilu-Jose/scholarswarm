from typing import List, Optional

from pydantic import BaseModel, Field


class Profile(BaseModel):
    name: str = "Rahul Sharma"
    degree: str = "B.Tech"
    field: str = "Computer Science & Engineering"
    cgpa: float = 8.2
    cgpa_scale: float = 10.0
    grad_year: int = 2026
    location: str = "Jalandhar, Punjab, India"
    nationality: str = "India"
    github: str = ""
    linkedin: str = ""
    extra_urls: List[str] = Field(default_factory=list)  # other supplied public profiles
    destinations: List[str] = Field(default_factory=lambda: ["Germany", "Canada", "Singapore"])
    target_degree: str = "masters"  # masters | phd
    research_interest: str = ""
    funding_need: str = "full"  # full | partial | none
    ielts_status: str = "none"  # none | planned | have
    ielts_score: Optional[float] = None
    work_years: float = 0.0
    resume_text: str = ""
    transcript_text: str = ""
    skills: List[str] = Field(default_factory=list)


class DraftRequest(BaseModel):
    run_id: str
    opportunity_id: str


class ExportRequest(BaseModel):
    title: str = "Statement of Purpose"
    text: str
    fmt: str = "docx"  # docx | pdf
