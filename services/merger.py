from typing import List, Dict, Any
from rapidfuzz import fuzz, process
from models.schemas import ParsedResume, Skill, Experience, Education, Project, PersonalInfo, MergeSettings
from collections import defaultdict


class ResumeMerger:
    """Intelligent resume merging with deduplication"""
    
    def merge(self, resumes: List[ParsedResume], settings: MergeSettings) -> ParsedResume:
        """Merge multiple resumes into one"""
        
        # Merge each section
        merged_personal = self._merge_personal_info([r.personal_info for r in resumes])
        merged_skills = self._merge_skills([r.skills for r in resumes], settings.deduplicate_threshold)
        merged_experience = self._merge_experience([r.experience for r in resumes])
        merged_education = self._merge_education([r.education for r in resumes])
        merged_projects = self._merge_projects([r.projects for r in resumes], settings.deduplicate_threshold)
        
        # Apply settings
        if settings.max_skills and len(merged_skills) > settings.max_skills:
            merged_skills = merged_skills[:settings.max_skills]
        
        return ParsedResume(
            personal_info=merged_personal,
            skills=merged_skills,
            experience=merged_experience,
            education=merged_education,
            projects=merged_projects
        )
    
    def _merge_personal_info(self, infos: List[PersonalInfo]) -> PersonalInfo:
        """Merge personal info - use most complete data"""
        merged = PersonalInfo()
        
        for info in infos:
            if info.name and not merged.name:
                merged.name = info.name
            if info.email and not merged.email:
                merged.email = info.email
            if info.phone and not merged.phone:
                merged.phone = info.phone
            if info.location and not merged.location:
                merged.location = info.location
            if info.linkedin and not merged.linkedin:
                merged.linkedin = info.linkedin
            if info.github and not merged.github:
                merged.github = info.github
            if info.website and not merged.website:
                merged.website = info.website
        
        return merged
    
    def _merge_skills(self, skill_lists: List[List[Skill]], threshold: int = 85) -> List[Skill]:
        """Merge skills with fuzzy deduplication and ranking"""
        skill_map = {}
        
        for skills in skill_lists:
            for skill in skills:
                normalized_name = skill.name.lower().strip()
                
                # Try to find existing similar skill
                matched_key = None
                if skill_map:
                    match = process.extractOne(
                        normalized_name,
                        skill_map.keys(),
                        scorer=fuzz.ratio,
                        score_cutoff=threshold
                    )
                    if match:
                        matched_key = match[0]
                
                if matched_key:
                    # Update existing skill
                    skill_map[matched_key]['frequency'] += 1
                    skill_map[matched_key]['confidence'] = max(
                        skill_map[matched_key]['confidence'],
                        skill.confidence
                    )
                else:
                    # Add new skill
                    skill_map[normalized_name] = {
                        'name': skill.name,
                        'category': skill.category,
                        'frequency': 1,
                        'confidence': skill.confidence
                    }
        
        # Convert back to Skill objects and sort by frequency and confidence
        merged_skills = [
            Skill(
                name=data['name'],
                category=data['category'],
                frequency=data['frequency'],
                confidence=data['confidence']
            )
            for data in skill_map.values()
        ]
        
        # Sort: higher frequency and confidence first
        merged_skills.sort(key=lambda s: (s.frequency, s.confidence), reverse=True)
        
        return merged_skills
    
    def _merge_experience(self, exp_lists: List[List[Experience]]) -> List[Experience]:
        """Merge work experience, removing duplicates"""
        seen_signatures = set()
        merged_experience = []
        
        for experiences in exp_lists:
            for exp in experiences:
                # Create signature for deduplication
                signature = f"{exp.company.lower()}_{exp.title.lower()}_{exp.start_date or ''}"
                
                if signature not in seen_signatures:
                    merged_experience.append(exp)
                    seen_signatures.add(signature)
        
        # Sort by date (most recent first) - handle None dates
        merged_experience.sort(
            key=lambda e: (e.current, e.start_date or "0000"),
            reverse=True
        )
        
        return merged_experience
    
    def _merge_education(self, edu_lists: List[List[Education]]) -> List[Education]:
        """Merge education, removing duplicates"""
        seen = set()
        merged_education = []
        
        for educations in edu_lists:
            for edu in educations:
                key = f"{edu.institution.lower()}_{edu.degree.lower()}"
                
                if key not in seen:
                    merged_education.append(edu)
                    seen.add(key)
        
        return merged_education
    
    def _merge_projects(self, proj_lists: List[List[Project]], threshold: int = 85) -> List[Project]:
        """Merge projects with fuzzy matching"""
        project_map = {}
        
        for projects in proj_lists:
            for proj in projects:
                normalized_name = proj.name.lower().strip()
                
                # Try fuzzy matching
                matched_key = None
                if project_map:
                    match = process.extractOne(
                        normalized_name,
                        project_map.keys(),
                        scorer=fuzz.ratio,
                        score_cutoff=threshold
                    )
                    if match:
                        matched_key = match[0]
                
                if matched_key:
                    # Merge descriptions if different
                    existing = project_map[matched_key]
                    if proj.description != existing.description:
                        existing.description += f" | {proj.description}"
                    # Merge technologies
                    existing.technologies = list(set(existing.technologies + proj.technologies))
                else:
                    project_map[normalized_name] = proj
        
        return list(project_map.values())
