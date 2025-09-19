import json
import re
import os
import asyncio
from typing import List, Optional
from pathlib import Path
import aiofiles
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from src.scrapers.base import BaseJobScraper
from src.models.job import Job

class LinkedInScraper(BaseJobScraper):
    """LinkedIn job scraper using SerpAPI and HTML parsing support."""
    
    def __init__(self, serp_api_key: Optional[str] = None):
        self.serp_api_key = serp_api_key or os.getenv("SERPAPI_KEY")
        self.samples_path = Path("data/samples/linkedin/")
    
    async def scrape_jobs(self, query: str, location: str = "", limit: int = 10) -> List[Job]:
        """Scrape LinkedIn jobs using SerpAPI or HTML samples."""
        if self.serp_api_key:
            return await self._scrape_via_serpapi(query, location, limit)
        else:
            print("No SerpAPI key found. Using HTML samples.")
            return await self._scrape_from_samples()
    
    async def _scrape_via_serpapi(self, query: str, location: str, limit: int) -> List[Job]:
        """Scrape jobs using SerpAPI."""
        try:
            search_params = {
                "engine": "google_jobs",
                "q": f"{query} site:linkedin.com",
                "location": location,
                "num": min(limit, 20),  # SerpAPI limit
                "api_key": self.serp_api_key
            }
            
            # Run the search in a thread to avoid blocking
            search_result = await asyncio.to_thread(self._perform_serp_search, search_params)
            
            jobs = []
            jobs_results = search_result.get("jobs_results", [])
            
            for job_data in jobs_results[:limit]:
                try:
                    job = self._normalize_serp_job_data(job_data)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    print(f"Error processing job data: {e}")
                    continue
            
            return jobs
            
        except Exception as e:
            print(f"SerpAPI scraping error: {e}")
            # Fallback to samples if API fails
            return await self._scrape_from_samples()
    
    def _perform_serp_search(self, params: dict) -> dict:
        """Perform SerpAPI search (blocking operation)."""
        search = GoogleSearch(params)
        return search.get_dict()
    
    def _normalize_serp_job_data(self, job_data: dict) -> Optional[Job]:
        """Normalize SerpAPI job data to Job model."""
        try:
            title = job_data.get("title", "")
            company = job_data.get("company_name", "")
            location = job_data.get("location", "")
            description = job_data.get("description", "")
            job_url = job_data.get("related_links", [{}])[0].get("link", "")
            
            if not title or not company:
                return None
            
            # Extract requirements from description
            requirements = self._extract_skills(description)
            
            return Job(
                title=title,
                company=company,
                requirements=requirements,
                location=location,
                description=description,
                url=job_url
            )
            
        except Exception as e:
            print(f"Error normalizing SerpAPI job data: {e}")
            return None
    
    async def _scrape_from_samples(self) -> List[Job]:
        """Scrape jobs from HTML samples (fallback method)."""
        jobs = []
        
        if not self.samples_path.exists():
            # Create sample data if directory doesn't exist
            await self._create_sample_data()
        
        for html_file in self.samples_path.glob("*.html"):
            try:
                async with aiofiles.open(html_file, 'r', encoding='utf-8') as f:
                    html_content = await f.read()
                
                job = self._parse_html_job(html_content)
                if job:
                    jobs.append(job)
            except Exception as e:
                print(f"Error reading sample file {html_file}: {e}")
                continue
        
        return jobs
    
    def _parse_html_job(self, html_content: str) -> Optional[Job]:
        """Parse job data from LinkedIn HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract job title
            title_elem = soup.find('h1', class_='top-card-layout__title') or soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else "Software Developer"
            
            # Extract company
            company_elem = soup.find('span', class_='topcard__flavor') or soup.find('a', class_='topcard__org-name-link')
            company = company_elem.get_text(strip=True) if company_elem else "Tech Company"
            
            # Extract location
            location_elem = soup.find('span', class_='topcard__flavor--bullet') or soup.find('span', {'data-test': 'job-location'})
            location = location_elem.get_text(strip=True) if location_elem else "Remote"
            
            # Extract requirements/skills from job description
            description_elem = soup.find('div', class_='show-more-less-html__markup') or soup.find('div', class_='description__text')
            description = description_elem.get_text() if description_elem else ""
            
            requirements = self._extract_skills(description)
            
            return Job(
                title=title,
                company=company,
                requirements=requirements,
                location=location,
                description=description
            )
        
        except Exception as e:
            print(f"Error parsing HTML job: {e}")
            return None
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from job description using enhanced pattern matching."""
        # Comprehensive list of technical skills
        technical_skills = [
            # Programming Languages
            'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'Swift', 'Kotlin',
            
            # Python Frameworks
            'Django', 'Flask', 'FastAPI', 'Tornado', 'Pyramid', 'Bottle',
            
            # JavaScript Frameworks/Libraries  
            'React', 'Vue', 'Angular', 'Node.js', 'Express', 'Next.js', 'Nuxt.js',
            
            # Cloud Platforms
            'AWS', 'Azure', 'GCP', 'Google Cloud', 'DigitalOcean', 'Heroku',
            
            # Databases
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'SQLite', 'DynamoDB', 'Cassandra',
            
            # DevOps & Tools
            'Docker', 'Kubernetes', 'Jenkins', 'GitLab CI', 'GitHub Actions', 'Terraform', 'Ansible',
            
            # Version Control
            'Git', 'GitHub', 'GitLab', 'Bitbucket',
            
            # APIs & Architecture
            'REST API', 'GraphQL', 'Microservices', 'gRPC', 'WebSocket',
            
            # Testing
            'pytest', 'Jest', 'Selenium', 'Cypress', 'Unit Testing', 'Integration Testing',
            
            # Machine Learning
            'Machine Learning', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas', 'NumPy', 'Jupyter',
            
            # Other Technologies
            'Linux', 'Unix', 'Nginx', 'Apache', 'RabbitMQ', 'Kafka', 'CI/CD'
        ]
        
        found_skills = set()
        text_lower = text.lower()
        
        # Direct matching
        for skill in technical_skills:
            if skill.lower() in text_lower:
                found_skills.add(skill)
        
        # Pattern-based matching for variations
        patterns = {
            'CI/CD': r'\b(ci/cd|continuous integration|continuous deployment|continuous delivery)\b',
            'REST API': r'\b(rest|restful|api)\b',
            'Machine Learning': r'\b(ml|machine learning|artificial intelligence|ai)\b',
            'Docker': r'\b(docker|containerization|containers)\b',
            'Kubernetes': r'\b(kubernetes|k8s|orchestration)\b',
            'AWS': r'\b(aws|amazon web services)\b',
            'Azure': r'\b(azure|microsoft azure)\b',
            'GCP': r'\b(gcp|google cloud|google cloud platform)\b'
        }
        
        for skill, pattern in patterns.items():
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        
        return list(found_skills)[:12]  # Limit to top 12 skills
    
    def normalize_job_data(self, raw_data: dict) -> Job:
        """Normalize raw job data to Job model."""
        return Job(
            title=raw_data.get('title', 'Unknown Position'),
            company=raw_data.get('company_name', raw_data.get('company', 'Unknown Company')),
            requirements=self._extract_skills(raw_data.get('description', '')),
            location=raw_data.get('location', 'Unknown Location'),
            description=raw_data.get('description', ''),
            url=raw_data.get('link', raw_data.get('url', ''))
        )
    
    async def _create_sample_data(self):
        """Create comprehensive sample LinkedIn HTML files for testing."""
        self.samples_path.mkdir(parents=True, exist_ok=True)
        
        samples = [
            {
                "filename": "senior_python_developer.html",
                "content": '''
                <!DOCTYPE html>
                <html>
                <head><title>Senior Python Developer - Acme Corp</title></head>
                <body>
                    <h1 class="top-card-layout__title">Senior Python Developer</h1>
                    <span class="topcard__flavor">Acme Corp</span>
                    <span class="topcard__flavor--bullet">Remote</span>
                    <div class="show-more-less-html__markup">
                        <p>We are looking for a skilled Senior Python Developer with 5+ years of experience. 
                        Strong expertise in Django, FastAPI, and Flask frameworks required. Experience with 
                        Docker containerization, Kubernetes orchestration, and AWS cloud services essential.
                        Knowledge of PostgreSQL, Redis, and CI/CD pipelines using Jenkins or GitHub Actions.
                        Must have experience with REST APIs, GraphQL, and microservices architecture.
                        React.js and JavaScript knowledge is a plus.</p>
                    </div>
                </body>
                </html>
                '''
            },
            {
                "filename": "fullstack_developer.html", 
                "content": '''
                <!DOCTYPE html>
                <html>
                <head><title>Full Stack Developer - TechStart Inc</title></head>
                <body>
                    <h1 class="top-card-layout__title">Full Stack Developer</h1>
                    <span class="topcard__flavor">TechStart Inc</span>
                    <span class="topcard__flavor--bullet">San Francisco, CA</span>
                    <div class="show-more-less-html__markup">
                        <p>Join our dynamic team as a Full Stack Developer! We need someone proficient in 
                        Python backend development with Django or Flask, and modern frontend technologies 
                        like React, Vue.js, or Angular. Experience with TypeScript, Node.js, and MongoDB 
                        required. Knowledge of Docker, AWS, and GitLab CI/CD is essential. Must understand 
                        REST APIs, WebSocket connections, and have experience with unit testing using pytest.</p>
                    </div>
                </body>
                </html>
                '''
            },
            {
                "filename": "devops_engineer.html",
                "content": '''
                <!DOCTYPE html>
                <html>
                <head><title>DevOps Engineer - CloudTech Solutions</title></head>
                <body>
                    <h1 class="top-card-layout__title">DevOps Engineer</h1>
                    <span class="topcard__flavor">CloudTech Solutions</span>
                    <span class="topcard__flavor--bullet">New York, NY</span>
                    <div class="show-more-less-html__markup">
                        <p>Seeking experienced DevOps Engineer to manage our cloud infrastructure. 
                        Strong experience with AWS, Azure, or GCP required. Must be proficient in 
                        Docker, Kubernetes, Terraform, and Ansible. Experience with CI/CD pipelines 
                        using Jenkins, GitLab CI, or GitHub Actions. Knowledge of monitoring tools, 
                        Linux systems administration, and Python scripting essential. MySQL and 
                        PostgreSQL database management experience preferred.</p>
                    </div>
                </body>
                </html>
                '''
            }
        ]
        
        for sample in samples:
            async with aiofiles.open(self.samples_path / sample["filename"], 'w', encoding='utf-8') as f:
                await f.write(sample["content"])