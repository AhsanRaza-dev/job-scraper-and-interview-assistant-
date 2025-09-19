from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import uuid
from src.services.cv_analyzer import CVAnalyzer
from src.models.cv import CV, CVAnalysisResult
from src.models.job import Job

router = APIRouter()
analyzer = CVAnalyzer()

@router.post("/upload", response_model=CV)
async def upload_cv(
    file: UploadFile = File(...),
    tenant_id: Optional[str] = Form(None)
):
    """Upload and process a CV (PDF or text)."""
    try:
        cv_id = str(uuid.uuid4())
        
        if file.content_type == "application/pdf":
            content = await file.read()
            cv = await analyzer.process_pdf_cv(content, cv_id, tenant_id)
        else:
            content = await file.read()
            text_content = content.decode('utf-8')
            cv = await analyzer.process_cv(text_content, cv_id, tenant_id)
        
        return cv
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CV: {str(e)}")

@router.post("/analyze", response_model=CVAnalysisResult)
async def analyze_cv_job_match(cv: CV, job: Job):
    """Analyze how well a CV matches a job posting."""
    try:
        analysis = await analyzer.analyze_cv_job_match(cv, job)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing CV: {str(e)}")
