from pydantic import BaseModel, Field
from typing import List

class InterviewQuestion(BaseModel):
    """Interview question model."""
    question: str = Field(..., description="Interview question text")
    type: str = Field(..., description="Question type (technical/scenario)")
    skill_focus: str = Field(..., description="Primary skill this question targets")

class InterviewAssessment(BaseModel):
    """Complete interview assessment model."""
    fit_score: int = Field(..., ge=0, le=100, description="Job fit score (0-100)")
    questions: List[str] = Field(..., description="List of interview questions")
    rejected: bool = Field(default=False, description="Whether candidate was rejected")
    rejection_reason: str = Field(default="", description="Reason for rejection if applicable")
    
    class Config:
        schema_extra = {
            "example": {
                "fit_score": 78,
                "questions": [
                    "What are Python decorators?",
                    "Explain Django ORM.",
                    "How would you design a CI/CD pipeline?",
                    "Scenario: Your API is slow in production. How do you debug?"
                ]
            }
        }