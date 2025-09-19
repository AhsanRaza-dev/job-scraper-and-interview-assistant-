
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class CV(BaseModel):
    """CV model for structured CV data."""
    id: str = Field(..., description="Unique CV identifier")
    content: str = Field(..., description="Full CV text content")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    experience: Optional[str] = Field(None, description="Experience summary")
    education: Optional[str] = Field(None, description="Education details")
    tenant_id: Optional[str] = Field(None, description="Tenant identifier for multi-tenancy")

class CVAnalysisResult(BaseModel):
    """CV analysis result model."""
    cv_id: str
    extracted_skills: List[str]
    fit_score: int = Field(..., ge=0, le=100, description="Job fit score (0-100)")
    summary: str = Field(..., description="Analysis summary")
    matched_requirements: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)