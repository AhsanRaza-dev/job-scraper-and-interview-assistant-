import asyncio
import os
from typing import List
from openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
import json
import re
from src.models.cv import CV, CVAnalysisResult
from src.models.job import Job
from src.models.interview import InterviewAssessment, InterviewQuestion

class InterviewQuestionParser(BaseOutputParser):
    """Parser for interview questions from LLM output."""
    
    def parse(self, text: str) -> List[str]:
        """Parse questions from LLM response."""
        questions = []
        
        # Try to extract JSON first
        try:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if 'questions' in data:
                    return data['questions']
        except:
            pass
        
        # Fallback to line-by-line parsing
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('- ') or line.startswith('• ') or 
                        line.startswith(('1.', '2.', '3.', '4.')) or
                        any(keyword in line.lower() for keyword in ['question', '?'])):
                # Clean up the question
                question = re.sub(r'^[-•]\s*', '', line)
                question = re.sub(r'^\d+\.\s*', '', question)
                question = re.sub(r'^(Question\s*\d*:?\s*)', '', question, flags=re.IGNORECASE)
                if question and len(question) > 10:
                    questions.append(question.strip())
        
        return questions[:4]  # Limit to 4 questions

class InterviewGenerator:
    """Interview question generator using HuggingFace model via OpenAI client."""
    
    def __init__(self):
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN environment variable is required")
            
        self.hf_client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=hf_token,
        )
        
        self.parser = InterviewQuestionParser()
    
    async def generate_interview_assessment(
        self, 
        cv_analysis: CVAnalysisResult, 
        job: Job
    ) -> InterviewAssessment:
        """Generate complete interview assessment."""
        
        # Check if candidate should be rejected
        if cv_analysis.fit_score < 50:
            return InterviewAssessment(
                fit_score=cv_analysis.fit_score,
                questions=[],
                rejected=True,
                rejection_reason=self._generate_rejection_message(job, cv_analysis.fit_score)
            )
        
        # Generate interview questions
        questions = await self._generate_questions(cv_analysis, job)
        
        return InterviewAssessment(
            fit_score=cv_analysis.fit_score,
            questions=questions,
            rejected=False
        )
    
    def _generate_rejection_message(self, job: Job, fit_score: int) -> str:
        """Generate a polite rejection message."""
        return (
            f"Thank you for your interest in the {job.title} position at {job.company}. "
            f"After careful review of your qualifications, we have decided to move forward "
            f"with other candidates whose experience more closely aligns with our current needs. "
            f"We encourage you to apply for future opportunities that match your skillset and "
            f"wish you the best in your job search."
        )
    
    async def _generate_questions(self, cv_analysis: CVAnalysisResult, job: Job) -> List[str]:
        """Generate interview questions based on CV-job match using HuggingFace model."""
        
        try:
            # Generate all questions in one comprehensive prompt
            prompt = self._create_comprehensive_prompt(cv_analysis, job)
            
            response = await asyncio.to_thread(
                self.hf_client.chat.completions.create,
                model="deepseek-ai/DeepSeek-R1:novita",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            questions_text = response.choices[0].message.content
            questions = self.parser.parse(questions_text)
            
            # Ensure we have exactly 4 questions
            if len(questions) < 4:
                fallback_questions = self._get_fallback_questions(job.title, cv_analysis.matched_requirements)
                questions.extend(fallback_questions)
            
            return questions[:4]
        
        except Exception as e:
            print(f"Error generating questions with HuggingFace: {e}")
            return self._get_fallback_questions(job.title, cv_analysis.matched_requirements)
    
    def _create_comprehensive_prompt(self, cv_analysis: CVAnalysisResult, job: Job) -> str:
        """Create a comprehensive prompt for generating all interview questions."""
        return f"""
        Generate exactly 4 interview questions for a {job.title} position at {job.company}.

        Candidate Profile:
        - Matched Skills: {', '.join(cv_analysis.matched_requirements)}
        - All Extracted Skills: {', '.join(cv_analysis.extracted_skills)}
        - Fit Score: {cv_analysis.fit_score}%

        Job Requirements: {', '.join(job.requirements)}

        Requirements:
        1. Generate exactly 3 technical questions focusing on the matched skills
        2. Generate exactly 1 scenario-based question related to real work situations
        3. Make questions specific to the role and candidate's background
        4. Ensure questions test practical knowledge, not just theory
        5. The scenario question should start with "Scenario:" 

        Format your response as a numbered list:
        1. [Technical Question 1]
        2. [Technical Question 2] 
        3. [Technical Question 3]
        4. [Scenario Question]

        Questions:
        """
    
    def _get_fallback_questions(self, job_title: str, matched_skills: List[str]) -> List[str]:
        """Get fallback questions if LLM generation fails."""
        
        # Base questions for different roles
        role_questions = {
            "python": [
                "What are Python decorators and how do you use them in practice?",
                "Explain the difference between list comprehensions and generator expressions.",
                "How do you handle exceptions in Python and what are best practices?"
            ],
            "fullstack": [
                "How do you optimize database queries in web applications?",
                "Explain the difference between SQL and NoSQL databases.",
                "What are the key principles of RESTful API design?"
            ],
            "devops": [
                "How do you implement blue-green deployment strategies?",
                "Explain Infrastructure as Code and its benefits.",
                "What are the key metrics you monitor in production systems?"
            ],
            "frontend": [
                "Explain React hooks and when you would use useState vs useEffect.",
                "How do you optimize frontend performance?",
                "What are the differences between server-side and client-side rendering?"
            ]
        }
        
        # Determine question category based on job title and skills
        job_lower = job_title.lower()
        questions = []
        
        if any(term in job_lower for term in ['python', 'backend', 'django', 'flask']):
            questions = role_questions["python"]
        elif any(term in job_lower for term in ['fullstack', 'full stack', 'full-stack']):
            questions = role_questions["fullstack"]
        elif any(term in job_lower for term in ['devops', 'sre', 'infrastructure']):
            questions = role_questions["devops"]
        elif any(term in job_lower for term in ['frontend', 'react', 'vue', 'angular']):
            questions = role_questions["frontend"]
        else:
            questions = role_questions["python"]  # Default
        
        # Customize based on matched skills
        if "Django" in matched_skills:
            questions[0] = "Explain Django's MTV architecture and how it differs from MVC."
        elif "React" in matched_skills:
            questions[0] = "What are React hooks and how do they improve functional components?"
        elif "Docker" in matched_skills:
            questions[1] = "How would you optimize a Docker image for production deployment?"
        
        # Add scenario question
        scenario_questions = [
            "Scenario: Your application is experiencing high memory usage in production. Walk me through your debugging process.",
            "Scenario: A critical API endpoint is responding slowly during peak hours. How do you identify and resolve the issue?",
            "Scenario: You need to migrate a large dataset with zero downtime. What approach would you take?",
            "Scenario: Your team needs to deploy a hotfix to production immediately. What steps do you follow?"
        ]
        
        questions.append(scenario_questions[0])
        return questions