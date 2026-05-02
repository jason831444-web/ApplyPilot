from pydantic import BaseModel, Field


class ResumeTailoringRead(BaseModel):
    tailored_summary: str = Field(max_length=1200)
    bullet_suggestions: list[str] = Field(default_factory=list, max_length=5)
    keywords_to_add: list[str] = Field(default_factory=list, max_length=30)
    skills_to_emphasize: list[str] = Field(default_factory=list, max_length=30)
    project_suggestions: list[str] = Field(default_factory=list, max_length=10)
    cautions: list[str] = Field(default_factory=list, max_length=10)
