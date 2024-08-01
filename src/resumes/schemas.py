from ninja import Router, Schema, Field
from typing import Optional, List

from projects.schemas import Project


class Resume(Schema):
    id: Optional[int] = None
    bio: Optional[str] = None
    hackathon_id: int
    tech: Optional[List[str]] = None
    soft: Optional[List[str]] = None
    github: Optional[str] = ''
    hh: Optional[str] = ''
    telegram: Optional[str] = ''
    personal_website: Optional[str] = ''
    pdf_link: Optional[str] = ''

class Error(Schema):
    details: str

class SuggestResumeSchema(Schema):
    link: str

class ResumeSuggestion(Schema):
    bio: Optional[str] = None
    hards: Optional[List[str]] = None
    softs: Optional[List[str]] = None