from typing import List, Optional

from pydantic import BaseModel, Field  # type: ignore[import]


class WorkExperience(BaseModel):
    company: str = Field(..., description="Company name")
    role: str = Field(..., description="Job title / role")
    duration: str = Field(..., description="e.g. Jan 2022 – Dec 2023")
    description: str = Field(..., description="Key responsibilities and achievements")


class Education(BaseModel):
    institution: str = Field(..., description="School or university name")
    degree: str = Field(..., description="Degree / qualification")
    year: str = Field(..., description="Graduation year or range")
    gpa: Optional[str] = Field(None, description="GPA if applicable")


class ResumeInput(BaseModel):
    full_name: str
    email: str
    phone: str
    location: str
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    objective: str = Field(..., description="Career objective or professional summary")
    experiences: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    certifications: Optional[List[str]] = Field(default_factory=list)
    template_style: str = Field("modern", description="modern | minimal | professional")


class ResumeOutput(BaseModel):
    generated_resume: str
    tips: List[str]
    word_count: int


# ── Internship Search Models ──────────────────────────────────────────────────


class InternshipListing(BaseModel):
    title: str = Field(..., description="Job title / internship role")
    company: str = Field(..., description="Company offering the internship")
    location: str = Field(..., description="Location (city, remote, hybrid)")
    description: str = Field(
        ..., description="Brief description of the role and responsibilities"
    )
    url: str = Field(..., description="Link to the job posting")
    match_reason: str = Field(
        ..., description="Why this internship matches the candidate's profile"
    )
    source: Optional[str] = Field(
        None, description="Job board source (LinkedIn, Indeed, etc.)"
    )


class InternshipSearchInput(BaseModel):
    resume_text: str = Field(
        ..., description="The full generated resume text in Markdown"
    )
    preferred_location: Optional[str] = Field(
        None, description="Preferred city / country or 'remote'"
    )
    num_results: int = Field(
        8, ge=1, le=20, description="Number of internship results to return"
    )
    extra_keywords: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional extra keywords to refine the search (e.g. 'fintech', 'AI')",
    )


class InternshipSearchOutput(BaseModel):
    internships: List[InternshipListing]
    search_summary: str = Field(
        ..., description="Plain-English summary of the search performed"
    )
    total_found: int = Field(..., description="Number of listings returned")
    skills_detected: List[str] = Field(
        default_factory=list,
        description="Key skills extracted from the resume that drove the search",
    )
    search_queries_used: List[str] = Field(
        default_factory=list,
        description="Actual search queries sent to the search engine",
    )
    serper_active: bool = Field(
        default=False,
        description="True when live web search via SerperDevTool was used",
    )
