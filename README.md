# Job Scraper and Interview Assistant Platform

A comprehensive platform for scraping LinkedIn job postings using SerpAPI, analyzing CVs using RAG with HuggingFace models, and generating tailored interview questions.

## 🌟 Features

- **LinkedIn Job Scraping**: Professional scraping using SerpAPI with fallback to HTML samples
- **CV Analysis with RAG**: Upload and analyze CVs using HuggingFace models and vector databases
- **Smart Job Matching**: Advanced fit scoring with fuzzy skill matching
- **AI Interview Questions**: Generate tailored technical and scenario questions using DeepSeek-R1
- **Multi-tenant Support**: Complete data isolation for different recruiters
- **RESTful API**: FastAPI with automatic documentation and validation
- **Production Ready**: Docker, health checks, and comprehensive error handling

## 🛠️ Technology Stack

- **AI/ML**: HuggingFace DeepSeek-R1 model via OpenAI-compatible API
- **Job Scraping**: SerpAPI for reliable LinkedIn job data
- **Backend**: FastAPI, Python 3.11
- **Vector DB**: FAISS for CV content indexing
- **Embeddings**: HuggingFace sentence-transformers
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions

## 🚀 Quick Start

### Prerequisites

1. **HuggingFace Token**: Get your token from [HuggingFace](https://huggingface.co/settings/tokens)
2. **SerpAPI Key**: Sign up at [SerpAPI](https://serpapi.com/) for job scraping
3. **Docker** and **Python 3.11+**

### Installation

#### 1. Clone the repository

```bash
git clone https://github.com/yourusername/job-scraper-platform.git
cd job-scraper-platform
```

#### 2. Set up environment

```bash
cp .env.example .env
# Edit .env and add your API keys:
# HF_TOKEN=your_huggingface_token
# SERPAPI_KEY=your_serpapi_key
```

#### 3. Run with Docker (Recommended)

```bash
docker-compose up --build
```

#### 4. Or run locally

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export HF_TOKEN=your_token_here
export SERPAPI_KEY=your_key_here
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Jobs Health**: http://localhost:8000/api/v1/jobs/health

## 📚 API Usage Examples

### 1. Scrape LinkedIn Jobs with SerpAPI

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/jobs/scrape?query=Senior%20Python%20Developer&location=Remote&limit=10"
```

**Response:**

```json
[
  {
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "requirements": ["Python", "Django", "AWS", "Docker", "PostgreSQL"],
    "location": "Remote",
    "description": "Looking for experienced Python developer...",
    "url": "https://linkedin.com/jobs/view/12345"
  }
]
```

### 2. Upload and Process CV

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/cv/upload" \
  -F "file=@resume.pdf" \
  -F "tenant_id=recruiter-123"
```

**Response:**

```json
{
  "id": "cv-uuid-123",
  "content": "Extracted CV text content...",
  "skills": ["Python", "Django", "React", "AWS", "Docker"],
  "tenant_id": "recruiter-123"
}
```

### 3. Generate Complete Interview Assessment

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/interview/complete-assessment" \
  -H "Content-Type: application/json" \
  -d '{
    "cv": {
      "id": "cv-123",
      "content": "Python developer with Django experience...",
      "skills": ["Python", "Django", "PostgreSQL"],
      "tenant_id": "recruiter-123"
    },
    "job": {
      "title": "Senior Python Developer",
      "company": "Tech Corp",
      "requirements": ["Python", "Django", "AWS"],
      "location": "Remote"
    }
  }'
```

**Success Response:**

```json
{
  "cv_analysis": {
    "cv_id": "cv-123",
    "extracted_skills": ["Python", "Django", "PostgreSQL"],
    "fit_score": 85,
    "summary": "Strong candidate with excellent Python and Django expertise...",
    "matched_requirements": ["Python", "Django"],
    "missing_requirements": ["AWS"]
  },
  "interview_assessment": {
    "fit_score": 85,
    "questions": [
      "Explain Django's ORM and how you would optimize database queries for large datasets.",
      "How do you implement caching strategies in Django applications?",
      "What are Python decorators and how would you use them in a web application?",
      "Scenario: Your Django application is experiencing slow response times during peak hours. Walk me through your debugging and optimization process."
    ],
    "rejected": false
  }
}
```

### 4. Rejection Example (Low Fit Score)

For candidates with `fit_score < 50`:

```json
{
  "cv_analysis": {
    "fit_score": 25,
    "matched_requirements": [],
    "missing_requirements": ["Python", "Django", "AWS"]
  },
  "interview_assessment": {
    "fit_score": 25,
    "questions": [],
    "rejected": true,
    "rejection_reason": "Thank you for your interest in the Senior Python Developer position at Tech Corp. After careful review of your qualifications, we have decided to move forward with other candidates whose experience more closely aligns with our current needs."
  }
}
```

## ⚙️ Configuration

### Required Environment Variables

```bash
# HuggingFace Token (Required)
HF_TOKEN=hf_your_token_here

# SerpAPI Key (Required for job scraping)
SERPAPI_KEY=your_serpapi_key_here
```

### Optional Configuration

```bash
# Application Settings
ENVIRONMENT=production
LOG_LEVEL=info

# Custom HuggingFace Model
HF_MODEL=deepseek-ai/DeepSeek-R1:novita

# Multi-tenant Settings
DEFAULT_TENANT_ID=default
```

## 🏗️ Architecture

### Key Components

1. **LinkedIn Scraper**: SerpAPI integration with HTML fallback
2. **CV Analyzer**: RAG-powered analysis using HuggingFace embeddings
3. **Interview Generator**: DeepSeek-R1 model for question generation
4. **Vector Database**: FAISS for CV content indexing
5. **Multi-tenant Support**: Isolated data per recruiter

### Data Flow

```
Job Query → SerpAPI → Normalized Jobs
    ↓
CV Upload → Text Extraction → Skill Analysis → Vector Storage
    ↓
Job + CV → Matching Analysis → Fit Score + Summary
    ↓
High Score → HuggingFace Model → Interview Questions
Low Score → Polite Rejection
```

## 📊 Sample Input/Output

### Job Scraping Output

```json
{
  "title": "Senior Python Developer",
  "company": "Acme Corp",
  "requirements": ["Python", "Django", "FastAPI", "Docker", "AWS"],
  "location": "Remote",
  "description": "Full job description...",
  "url": "https://linkedin.com/jobs/view/12345"
}
```

### Interview Assessment Output

```json
{
  "fit_score": 78,
  "questions": [
    "What are Python decorators and how do you use them in practice?",
    "Explain Django's MTV architecture and how it differs from MVC.",
    "How would you design a scalable microservices architecture?",
    "Scenario: Your API is experiencing high latency. How do you diagnose and resolve the issue?"
  ],
  "rejected": false
}
```

## 🧪 Development

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v --cov=src

# Run specific test file
pytest tests/test_scrapers.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Check linting
flake8 src/ tests/ --max-line-length=100

# Type checking
mypy src/
```

### Local Development Setup

```bash
# 1. Set up virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export HF_TOKEN=your_token
export SERPAPI_KEY=your_key

# 4. Run development server
uvicorn src.api.main:app --reload

# 5. Test the API
curl http://localhost:8000/health
```

## 🚀 Production Deployment

### Docker Production Build

```bash
# Build production image
docker build -t job-scraper-platform:latest .

# Run with production settings
docker run -d \
  -p 8000:8000 \
  -e HF_TOKEN=your_token \
  -e SERPAPI_KEY=your_key \
  -e ENVIRONMENT=production \
  job-scraper-platform:latest
```

### Environment-Specific Configs

```bash
# Development
ENVIRONMENT=development
LOG_LEVEL=debug

# Production
ENVIRONMENT=production
LOG_LEVEL=info
```

## 🏢 Multi-Tenant Usage

The platform supports complete data isolation between different recruiters:

```python
# Upload CV with tenant ID
cv = await analyzer.process_cv(content, cv_id, tenant_id="company-123")

# Data is isolated per tenant
# company-123 cannot access company-456's data
```

## 🔗 API Endpoints

### Jobs

- `GET /api/v1/jobs/scrape` - Scrape LinkedIn jobs
- `POST /api/v1/jobs/normalize` - Normalize job data
- `GET /api/v1/jobs/sample-jobs` - Get sample jobs
- `GET /api/v1/jobs/health` - Job service health check

### CV Analysis

- `POST /api/v1/cv/upload` - Upload and process CV
- `POST /api/v1/cv/analyze` - Analyze CV against job

### Interview

- `POST /api/v1/interview/generate` - Generate interview questions
- `POST /api/v1/interview/complete-assessment` - Full CV-job assessment

## ✨ Bonus Features

- **Smart Rejection**: Candidates with `fit_score < 50` receive polite rejection
- **Skill Validation**: Skills extracted and validated from actual CV content
- **Multi-tenant**: Complete data isolation between recruiters
- **Fuzzy Matching**: Advanced skill matching (e.g., "React" matches "React.js")
- **Professional Error Handling**: Comprehensive error responses and fallbacks

## 🔧 Troubleshooting

### Common Issues

#### 1. "HF_TOKEN not found"

- **Solution**: Set your HuggingFace token: `export HF_TOKEN=your_token`

#### 2. "No jobs found" when scraping

- Check your SerpAPI key: `export SERPAPI_KEY=your_key`
- Verify SerpAPI quota and billing

#### 3. CV processing fails

- Ensure PDF is readable and not password-protected
- Check file size (max 10MB recommended)

#### 4. Interview questions are generic

- Verify HF_TOKEN is valid and has API access
- Check HuggingFace model availability

### Health Checks

```bash
# General health
curl http://localhost:8000/health

# Jobs service health
curl http://localhost:8000/api/v1/jobs/health

# Check if APIs are configured
curl http://localhost:8000/api/v1/jobs/health | jq '.serpapi_configured'
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Format code (`black src/ tests/`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check `/docs` endpoint when running
- **Issues**: Create GitHub issues for bugs/features
- **API Help**: Use interactive docs at `/docs`
- **Examples**: Check test files for usage patterns

---

**Ready to use with HuggingFace DeepSeek-R1 and SerpAPI for job scraping and AI-powered interview generation!** 🚀
