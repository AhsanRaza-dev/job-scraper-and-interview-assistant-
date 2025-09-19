from typing import Optional
from src.services.cv_analyzer import CVAnalyzer
from src.services.interview_generator import InterviewGenerator
from src.models.cv import CV, CVAnalysisResult
from src.models.job import Job
from src.models.interview import InterviewAssessment

class MatchingService:
    """Service to orchestrate CV-job matching and interview generation."""
    
    def __init__(self, cv_analyzer: CVAnalyzer, interview_generator: InterviewGenerator):
        self.cv_analyzer = cv_analyzer
        self.interview_generator = interview_generator
    
    async def process_complete_assessment(
        self, 
        cv: CV, 
        job: Job
    ) -> dict:
        """Process complete CV-job assessment with interview questions."""
        
        # Analyze CV-job match
        cv_analysis = await self.cv_analyzer.analyze_cv_job_match(cv, job)
        
        # Generate interview assessment
        interview_assessment = await self.interview_generator.generate_interview_assessment(
            cv_analysis, job
        )
        
        return {
            "cv_analysis": cv_analysis.dict(),
            "interview_assessment": interview_assessment.dict()
        }