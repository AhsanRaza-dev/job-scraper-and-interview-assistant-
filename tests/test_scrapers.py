import pytest
from src.scrapers.linkedin_scraper import LinkedInScraper
from src.models.job import Job

@pytest.fixture
def scraper():
    return LinkedInScraper()

@pytest.mark.asyncio
async def test_scrape_from_samples(scraper):
    """Test scraping from HTML samples."""
    jobs = await scraper.scrape_jobs("Python Developer")
    assert isinstance(jobs, list)
    
    if jobs:  # If sample data exists
        job = jobs[0]
        assert isinstance(job, Job)
        assert job.title
        assert job.company
        assert isinstance(job.requirements, list)

def test_normalize_job_data(scraper):
    """Test job data normalization."""
    raw_data = {
        'title': 'Senior Python Developer',
        'company_name': 'Tech Corp',
        'description': 'Python Django FastAPI Docker experience required',
        'location': 'San Francisco, CA'
    }
    
    job = scraper.normalize_job_data(raw_data)
    assert job.title == 'Senior Python Developer'
    assert job.company == 'Tech Corp'
    assert 'Python' in job.requirements
    assert job.location == 'San Francisco, CA'