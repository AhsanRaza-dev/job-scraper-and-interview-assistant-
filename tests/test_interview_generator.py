import pytest
from src.services.interview_generator import InterviewGenerator
from src.models.cv import CVAnalysisResult
from src.models.job import Job

@pytest.fixture
def generator():
    return InterviewGenerator()

@pytest.fixture
def high_score_analysis():
    return CVAnalysisResult(
        cv_id="test-cv",
        extracted_skills=["Python", "Django", "FastAPI"],
        fit_score=85,
        summary="Good match",
        matched_requirements=["Python", "Django"],
        missing_requirements=["React"]
    )

@pytest.fixture
def low_score_analysis():
    return CVAnalysisResult(
        cv_id="test-cv",
        extracted_skills=["Java", "Spring"],
        fit_score=25,
        summary="Poor match",
        matched_requirements=[],
        missing_requirements=["Python", "Django"]
    )

@pytest.fixture
def sample_job():
    return Job(
        title="Python Developer",
        company="Tech Corp",
        requirements=["Python", "Django", "React"],
        location="Remote"
    )

@pytest.mark.asyncio
async def test_generate_interview_high_score(generator, high_score_analysis, sample_job):
    """Test interview generation for high-scoring candidate."""
    assessment = await generator.generate_interview_assessment(high_score_analysis, sample_job)
    
    assert assessment.fit_score == 85
    assert not assessment.rejected
    assert len(assessment.questions) == 4
    assert assessment.rejection_reason == ""

@pytest.mark.asyncio
async def test_generate_interview_low_score(generator, low_score_analysis, sample_job):
    """Test interview generation for low-scoring candidate."""
    assessment = await generator.generate_interview_assessment(low_score_analysis, sample_job)
    
    assert assessment.fit_score == 25
    assert assessment.rejected
    assert len(assessment.questions) == 0
    assert assessment.rejection_reason != ""