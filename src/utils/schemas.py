from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class JobScrapingRequest(BaseModel):
    query: str
    location: str = ""
    limit: int = 10

class CVUploadResponse(BaseModel):
    cv_id: str
    extracted_skills: List[str]
    message: str

class MatchingRequest(BaseModel):
    cv_id: str
    job_data: Dict[str, Any]

class ValidationError(BaseModel):
    field: str
    message: str

class APIResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[ValidationError]] = None
