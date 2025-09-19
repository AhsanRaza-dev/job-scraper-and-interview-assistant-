import pytest
from src.services.cv_analyzer import CVAnalyzer
from src.models.cv import CV
from src.models.job import Job

@pytest.fixture
def analyzer():
    return CVAnalyzer()

@pytest.fixture
def sample_cv():
    return CV(
        id="test-cv-1",
        content="Experienced Python developer with Django, FastAPI, and Docker experience. "
                "Worked with AWS, PostgreSQL, and CI/CD pipelines.",
        skills=["Python", "Django", "FastAPI", "Docker", "AWS", "PostgreSQL"],
        tenant_id="test-tenant"
    )

@pytest.fixture
def sample_job():
    return Job(
        title="Python Developer",
        company="Tech Corp",
        requirements=["Python", "Django", "Docker", "AWS"],
        location="Remote"
    )

@pytest.mark.asyncio
async def test_process_cv(analyzer):
    """Test CV processing."""
    cv_content = "Python developer with Django and React experience"
    cv = await analyzer.process_cv(cv_content, "test-cv", "test-tenant")
    
    assert cv.id == "test-cv"
    assert cv.content == cv_content
    assert "Python" in cv.skills

@pytest.mark.asyncio
async def test_analyze_cv_job_match(analyzer, sample_cv, sample_job):
    """Test CV-job matching analysis."""
    result = await analyzer.analyze_cv_job_match(sample_cv, sample_job)
    
    assert result.cv_id == sample_cv.id
    assert 0 <= result.fit_score <= 100
    assert len(result.matched_requirements) > 0
    assert result.summary