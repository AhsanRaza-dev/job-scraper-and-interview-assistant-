import asyncio
import os
from typing import List, Dict, Any
import numpy as np
from pathlib import Path
import PyPDF2
import io
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from src.models.cv import CV, CVAnalysisResult
from src.models.job import Job
import re

class CVAnalyzer:
    """CV analysis service with RAG capabilities using HuggingFace model."""
    
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize HuggingFace OpenAI client
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN environment variable is required")
            
        self.hf_client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=hf_token,
        )
        
        # Initialize LangChain with HuggingFace client
        self.llm = ChatOpenAI(
            openai_api_base="https://router.huggingface.co/v1",
            openai_api_key=hf_token,
            model_name="deepseek-ai/DeepSeek-R1:novita",
            temperature=0.1
        )
        
        self.vector_stores: Dict[str, FAISS] = {}
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    async def process_cv(self, cv_content: str, cv_id: str, tenant_id: str = None) -> CV:
        """Process CV content and extract information."""
        # Extract skills from CV
        skills = await self._extract_skills_from_cv(cv_content)
        
        # Create CV object
        cv = CV(
            id=cv_id,
            content=cv_content,
            skills=skills,
            tenant_id=tenant_id
        )
        
        # Store in vector database
        await self._store_cv_in_vector_db(cv)
        
        return cv
    
    async def process_pdf_cv(self, pdf_content: bytes, cv_id: str, tenant_id: str = None) -> CV:
        """Process PDF CV and extract text content."""
        text_content = self._extract_text_from_pdf(pdf_content)
        return await self.process_cv(text_content, cv_id, tenant_id)
    
    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            raise ValueError(f"Error extracting text from PDF: {e}")
    
    async def _extract_skills_from_cv(self, cv_content: str) -> List[str]:
        """Extract skills from CV content using pattern matching and HuggingFace LLM."""
        # Technical skills pattern matching
        technical_skills = [
            'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'Ruby',
            'Django', 'Flask', 'FastAPI', 'React', 'Vue', 'Angular', 'Node.js', 'Express',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
            'Git', 'CI/CD', 'Jenkins', 'Linux', 'REST API', 'GraphQL', 'Machine Learning', 
            'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn', 'Microservices'
        ]
        
        found_skills = []
        cv_lower = cv_content.lower()
        
        for skill in technical_skills:
            if skill.lower() in cv_lower:
                found_skills.append(skill)
        
        # Use HuggingFace LLM for additional skill extraction
        try:
            prompt = f"""
            Extract technical skills from this CV content. Return only the skills as a comma-separated list.
            Focus on programming languages, frameworks, tools, and technologies.
            
            CV Content:
            {cv_content[:2000]}
            
            Skills:
            """
            
            response = await asyncio.to_thread(
                self.hf_client.chat.completions.create,
                model="deepseek-ai/DeepSeek-R1:novita",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            llm_response = response.choices[0].message.content
            if llm_response:
                llm_skills = [skill.strip() for skill in llm_response.split(',')]
                # Filter and validate skills
                valid_skills = [skill for skill in llm_skills if skill and len(skill) > 2 and len(skill) < 30]
                found_skills.extend(valid_skills)
        
        except Exception as e:
            print(f"HuggingFace skill extraction failed: {e}")
        
        # Remove duplicates and return
        unique_skills = list(set(found_skills))
        return unique_skills[:15]  # Limit to top 15 skills
    
    async def _store_cv_in_vector_db(self, cv: CV):
        """Store CV in vector database for RAG."""
        try:
            # Split text into chunks
            texts = self.text_splitter.split_text(cv.content)
            
            # Create vector store key (include tenant for multi-tenancy)
            store_key = f"{cv.tenant_id or 'default'}_{cv.id}"
            
            # Create or update vector store
            if store_key in self.vector_stores:
                # Add to existing store
                self.vector_stores[store_key].add_texts(texts)
            else:
                # Create new vector store
                self.vector_stores[store_key] = await asyncio.to_thread(
                    FAISS.from_texts, texts, self.embeddings
                )
        
        except Exception as e:
            print(f"Error storing CV in vector DB: {e}")
    
    async def analyze_cv_job_match(self, cv: CV, job: Job) -> CVAnalysisResult:
        """Analyze how well a CV matches a job posting."""
        # Calculate fit score
        fit_score = self._calculate_fit_score(cv.skills, job.requirements)
        
        # Find matched and missing requirements
        matched_requirements = []
        for req in job.requirements:
            for skill in cv.skills:
                if req.lower() == skill.lower() or req.lower() in skill.lower() or skill.lower() in req.lower():
                    matched_requirements.append(req)
                    break
        
        missing_requirements = [req for req in job.requirements if req not in matched_requirements]
        
        # Generate summary using RAG
        summary = await self._generate_match_summary(cv, job, fit_score)
        
        return CVAnalysisResult(
            cv_id=cv.id,
            extracted_skills=cv.skills,
            fit_score=fit_score,
            summary=summary,
            matched_requirements=matched_requirements,
            missing_requirements=missing_requirements
        )
    
    def _calculate_fit_score(self, cv_skills: List[str], job_requirements: List[str]) -> int:
        """Calculate job fit score based on skill matching with fuzzy matching."""
        if not job_requirements:
            return 50  # Default score if no requirements
        
        cv_skills_lower = [skill.lower() for skill in cv_skills]
        matched_count = 0
        
        for req in job_requirements:
            req_lower = req.lower()
            # Direct match or partial match
            for cv_skill in cv_skills_lower:
                if (req_lower == cv_skill or 
                    req_lower in cv_skill or 
                    cv_skill in req_lower or
                    self._skills_are_related(req_lower, cv_skill)):
                    matched_count += 1
                    break
        
        fit_percentage = (matched_count / len(job_requirements)) * 100
        
        # Add bonus for extra relevant skills (up to 10 points)
        extra_skills_bonus = min(len(cv_skills) - matched_count, 5) * 2
        
        return min(int(fit_percentage + extra_skills_bonus), 100)
    
    def _skills_are_related(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are related (e.g., 'react' and 'react.js')."""
        related_skills = {
            'react': ['react.js', 'reactjs'],
            'node': ['node.js', 'nodejs'],
            'vue': ['vue.js', 'vuejs'],
            'angular': ['angularjs'],
            'javascript': ['js'],
            'typescript': ['ts'],
            'python': ['py'],
            'postgresql': ['postgres'],
            'mongodb': ['mongo'],
            'ci/cd': ['continuous integration', 'continuous deployment'],
            'aws': ['amazon web services'],
            'gcp': ['google cloud platform', 'google cloud'],
            'azure': ['microsoft azure']
        }
        
        for main_skill, variations in related_skills.items():
            if ((main_skill in skill1 and any(var in skill2 for var in variations)) or
                (main_skill in skill2 and any(var in skill1 for var in variations))):
                return True
        
        return False
    
    async def _generate_match_summary(self, cv: CV, job: Job, fit_score: int) -> str:
        """Generate match summary using RAG with HuggingFace model."""
        try:
            store_key = f"{cv.tenant_id or 'default'}_{cv.id}"
            if store_key not in self.vector_stores:
                return f"Candidate shows {fit_score}% compatibility with the position requirements based on skill analysis."
            
            # Create context from CV using vector search
            retriever = self.vector_stores[store_key].as_retriever(search_kwargs={"k": 3})
            relevant_docs = await asyncio.to_thread(
                retriever.get_relevant_documents, 
                f"skills experience {job.title}"
            )
            
            context = " ".join([doc.page_content for doc in relevant_docs])[:1500]
            
            prompt = f"""
            Analyze this candidate's fit for a {job.title} position at {job.company}.
            
            Job Requirements: {', '.join(job.requirements)}
            Candidate Context: {context}
            Fit Score: {fit_score}%
            
            Provide a brief professional summary (2-3 sentences) of the match quality, highlighting strengths and any gaps.
            """
            
            response = await asyncio.to_thread(
                self.hf_client.chat.completions.create,
                model="deepseek-ai/DeepSeek-R1:novita",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.2
            )
            
            summary = response.choices[0].message.content.strip()
            return summary if summary else f"Candidate demonstrates {fit_score}% alignment with the position requirements."
        
        except Exception as e:
            print(f"Error generating match summary: {e}")
            return f"Candidate shows {fit_score}% compatibility with the position requirements."
