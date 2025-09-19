from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import os
from src.models.job import Job
from src.scrapers.linkedin_scraper import LinkedInScraper

router = APIRouter()

def get_scraper():
    """Dependency to get LinkedIn scraper with SerpAPI key."""
    return LinkedInScraper(serp_api_key=os.getenv("SERPAPI_KEY"))

@router.get("/scrape", response_model=List[Job])
async def scrape_jobs(
    query: str = Query(..., description="Job search query (e.g., 'Python Developer')"),
    location: str = Query("", description="Job location (e.g., 'Remote', 'San Francisco')"),
    limit: int = Query(10, ge=1, le=50, description="Number of jobs to scrape"),
    scraper: LinkedInScraper = Depends(get_scraper)
):
    """
    Scrape jobs from LinkedIn using SerpAPI.
    
    - **query**: Job search terms (required)
    - **location**: Geographic location filter (optional)  
    - **limit**: Maximum number of jobs to return (1-50)
    
    Returns a list of normalized job objects with skills extracted from descriptions.
    """
    try:
        jobs = await scraper.scrape_jobs(query, location, limit)
        
        if not jobs:
            raise HTTPException(
                status_code=404, 
                detail="No jobs found. Please try different search terms or check your SerpAPI configuration."
            )
        
        return jobs
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error scraping jobs: {str(e)}"
        )

@router.post("/normalize", response_model=Job)
async def normalize_job_data(
    raw_data: dict,
    scraper: LinkedInScraper = Depends(get_scraper)
):
    """
    Normalize raw job data to standardized Job model format.
    
    Accepts raw job data from various sources and converts it to the standard format
    with extracted skills and requirements.
    """
    try:
        job = scraper.normalize_job_data(raw_data)
        return job
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error normalizing job data: {str(e)}"
        )

@router.get("/sample-jobs", response_model=List[Job])
async def get_sample_jobs(scraper: LinkedInScraper = Depends(get_scraper)):
    """
    Get sample jobs for testing purposes.
    
    Returns sample job data from HTML files if SerpAPI is not configured.
    Useful for development and testing.
    """
    try:
        jobs = await scraper._scrape_from_samples()
        return jobs
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching sample jobs: {str(e)}"
        )

@router.get("/health")
async def jobs_health_check(scraper: LinkedInScraper = Depends(get_scraper)):
    """Check if job scraping service is healthy."""
    serpapi_configured = bool(scraper.serp_api_key)
    
    return {
        "status": "healthy",
        "serpapi_configured": serpapi_configured,
        "scraper_type": "SerpAPI" if serpapi_configured else "HTML Samples"
    }