from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None


class Skill(BaseModel):
    name: str
    category: Optional[str] = "general"
    frequency: int = 1
    confidence: float = 1.0


class Experience(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: bool = False
    description: List[str] = []
    technologies: List[str] = []


class Education(BaseModel):
    degree: str
    institution: str
    location: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[str] = None


class Project(BaseModel):
    name: str
    description: str
    technologies: List[str] = []
    url: Optional[str] = None


class ParsedResume(BaseModel):
    personal_info: PersonalInfo
    summary: Optional[str] = None
    skills: List[Skill] = []
    experience: List[Experience] = []
    education: List[Education] = []
    projects: List[Project] = []
    certifications: List[str] = []
    languages: List[str] = []


class MergeSettings(BaseModel):
    include_sections: List[str] = ["personal_info", "skills", "experience", "education", "projects"]
    max_skills: int = 30
    sort_experience_by: str = "date"  # "date" or "relevance"
    deduplicate_threshold: int = 85  # Fuzzy match threshold (0-100)


class MergeRequest(BaseModel):
    resumes: List[ParsedResume]
    settings: Optional[MergeSettings] = MergeSettings()


class MergeResponse(BaseModel):
    success: bool
    merged_resume: ParsedResume
