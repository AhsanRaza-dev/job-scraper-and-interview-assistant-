from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from src.services.cv_analyzer import CVAnalyzer
from src.services.interview_generator import InterviewGenerator
from src.services.matching_service import MatchingService
from src.scrapers.linkedin_scraper import LinkedInScraper

# Global service instances
cv_analyzer = CVAnalyzer()
interview_generator = InterviewGenerator()
matching_service = MatchingService(cv_analyzer, interview_generator)
linkedin_scraper = LinkedInScraper()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Job Scraper and Interview Assistant Platform...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Job Scraper and Interview Assistant Platform",
    description="A platform for scraping jobs, analyzing CVs, and generating interview questions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from src.api.routes.jobs import router as jobs_router
from src.api.routes.cv import router as cv_router
from src.api.routes.interview import router as interview_router

app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(cv_router, prefix="/api/v1/cv", tags=["cv"])
app.include_router(interview_router, prefix="/api/v1/interview", tags=["interview"])

@app.get("/")
async def root():
    return {"message": "Job Scraper and Interview Assistant Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)