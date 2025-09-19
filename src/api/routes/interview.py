from fastapi import APIRouter, HTTPException
from src.services.matching_service import MatchingService
from src.services.cv_analyzer import CVAnalyzer
from src.services.interview_generator import InterviewGenerator
from src.models.cv import CV
from src.models.job import Job
from src.models.interview import InterviewAssessment

router = APIRouter()
cv_analyzer = CVAnalyzer()
interview_generator = InterviewGenerator()
matching_service = MatchingService(cv_analyzer, interview_generator)

@router.post("/generate", response_model=InterviewAssessment)
async def generate_interview_questions(cv: CV, job: Job):
    """Generate interview questions based on CV-job match."""
    try:
        # First analyze the CV-job match
        cv_analysis = await cv_analyzer.analyze_cv_job_match(cv, job)
        
        # Generate interview assessment
        assessment = await interview_generator.generate_interview_assessment(cv_analysis, job)
        
        return assessment
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating interview: {str(e)}")

@router.post("/complete-assessment")
async def complete_assessment(cv: CV, job: Job):
    """Get complete assessment including CV analysis and interview questions."""
    try:
        result = await matching_service.process_complete_assessment(cv, job)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing assessment: {str(e)}")
