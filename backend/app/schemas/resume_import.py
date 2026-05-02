from pydantic import BaseModel, Field


class ResumeImportRead(BaseModel):
    resume_text: str = Field(max_length=30000)
    skills_suggestions: list[str] = Field(default_factory=list, max_length=100)
    projects_suggestions: list[str] = Field(default_factory=list, max_length=10)
    experience_summary_suggestion: str = Field(default="", max_length=5000)
