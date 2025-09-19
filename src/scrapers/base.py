from abc import ABC, abstractmethod
from typing import List
from src.models.job import Job

class BaseJobScraper(ABC):
    """Abstract base class for job scrapers."""
    
    @abstractmethod
    async def scrape_jobs(self, query: str, location: str = "", limit: int = 10) -> List[Job]:
        """Scrape jobs based on query and location."""
        pass
    
    @abstractmethod
    def normalize_job_data(self, raw_data: dict) -> Job:
        """Normalize raw job data to Job model."""
        pass