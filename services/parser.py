import re
from typing import Dict, Any, List
import pdfplumber
from docx import Document
from models.schemas import ParsedResume, PersonalInfo, Skill, Experience, Education, Project


class ResumeParser:
    """Parse PDF and DOCX resumes into structured data"""
    
    def __init__(self):
        # Common regex patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'(\+?\d{1,3}[-.\s]?)?$$?\d{3}$$?[-.\s]?\d{3}[-.\s]?\d{4}'
        self.linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        self.github_pattern = r'github\.com/[\w-]+'
        
        # Common skill keywords (expand this list)
        self.skill_keywords = {
            'programming': ['python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'go', 'rust', 'typescript'],
            'frontend': ['react', 'vue', 'angular', 'html', 'css', 'tailwind', 'bootstrap', 'sass', 'next.js', 'nuxt'],
            'backend': ['node.js', 'express', 'django', 'flask', 'fastapi', 'spring', 'rails', '.net'],
            'database': ['postgresql', 'mysql', 'mongodb', 'redis', 'sqlite', 'dynamodb', 'firebase'],
            'cloud': ['aws', 'azure', 'gcp', 'vercel', 'heroku', 'docker', 'kubernetes'],
            'tools': ['git', 'jira', 'figma', 'postman', 'jenkins', 'github actions']
        }
    
    def parse_resume(self, file_path: str) -> ParsedResume:
        """Main parsing method"""
        if file_path.endswith('.pdf'):
            text = self._extract_from_pdf(file_path)
        elif file_path.endswith('.docx'):
            text = self._extract_from_docx(file_path)
        else:
            raise ValueError("Unsupported file format")
        
        # Parse sections
        personal_info = self._parse_personal_info(text)
        skills = self._parse_skills(text)
        experience = self._parse_experience(text)
        education = self._parse_education(text)
        projects = self._parse_projects(text)
        
        return ParsedResume(
            personal_info=personal_info,
            skills=skills,
            experience=experience,
            education=education,
            projects=projects
        )
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    
    def _parse_personal_info(self, text: str) -> PersonalInfo:
        """Extract personal information"""
        lines = text.split('\n')
        
        # Assume first non-empty line is the name
        name = next((line.strip() for line in lines if line.strip()), None)
        
        # Extract email
        email_match = re.search(self.email_pattern, text)
        email = email_match.group(0) if email_match else None
        
        # Extract phone
        phone_match = re.search(self.phone_pattern, text)
        phone = phone_match.group(0) if phone_match else None
        
        # Extract LinkedIn
        linkedin_match = re.search(self.linkedin_pattern, text, re.IGNORECASE)
        linkedin = linkedin_match.group(0) if linkedin_match else None
        
        # Extract GitHub
        github_match = re.search(self.github_pattern, text, re.IGNORECASE)
        github = github_match.group(0) if github_match else None
        
        return PersonalInfo(
            name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github
        )
    
    def _parse_skills(self, text: str) -> List[Skill]:
        """Extract skills using keyword matching"""
        text_lower = text.lower()
        found_skills = []
        
        for category, keywords in self.skill_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_skills.append(Skill(
                        name=keyword.title(),
                        category=category,
                        frequency=1,
                        confidence=0.9
                    ))
        
        return found_skills
    
    def _parse_experience(self, text: str) -> List[Experience]:
        """Extract work experience (basic implementation)"""
        experiences = []
        
        # Look for experience section
        exp_patterns = [
            r'(?:experience|work history|employment)(.*?)(?:education|skills|projects|$)',
            r'(?:professional experience)(.*?)(?:education|skills|$)'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                exp_text = match.group(1)
                # Simple extraction - split by company/role indicators
                lines = exp_text.split('\n')
                
                current_exp = None
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Heuristic: lines with dates often indicate new experience entry
                    if re.search(r'\d{4}', line):
                        if current_exp:
                            experiences.append(current_exp)
                        
                        current_exp = Experience(
                            title=line.split('|')[0].strip() if '|' in line else line,
                            company=line.split('|')[1].strip() if '|' in line and len(line.split('|')) > 1 else "Unknown",
                            description=[]
                        )
                    elif current_exp:
                        current_exp.description.append(line)
                
                if current_exp:
                    experiences.append(current_exp)
                
                break
        
        return experiences
    
    def _parse_education(self, text: str) -> List[Education]:
        """Extract education"""
        education = []
        
        # Look for education section
        edu_pattern = r'(?:education)(.*?)(?:experience|skills|projects|$)'
        match = re.search(edu_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            edu_text = match.group(1)
            lines = edu_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:  # Skip short lines
                    education.append(Education(
                        degree=line,
                        institution="Parsed from resume"
                    ))
        
        return education
    
    def _parse_projects(self, text: str) -> List[Project]:
        """Extract projects"""
        projects = []
        
        # Look for projects section
        proj_pattern = r'(?:projects)(.*?)(?:experience|education|skills|$)'
        match = re.search(proj_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            proj_text = match.group(1)
            lines = proj_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:
                    projects.append(Project(
                        name=line.split('-')[0].strip() if '-' in line else line,
                        description=line.split('-')[1].strip() if '-' in line else line
                    ))
        
        return projects
