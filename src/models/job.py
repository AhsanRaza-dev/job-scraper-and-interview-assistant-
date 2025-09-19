from pydantic import BaseModel, Field
from typing import List, Optional

class Job(BaseModel):
    """Job model for structured job data."""
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    requirements: List[str] = Field(default_factory=list, description="List of job requirements/skills")
    location: str = Field(..., description="Job location")
    description: Optional[str] = Field(None, description="Full job description")
    url: Optional[str] = Field(None, description="Job posting URL")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Python Developer",
                "company": "Acme Corp",
                "requirements": ["Python", "Django", "CI/CD"],
                "location": "Remote"
            }
        }
