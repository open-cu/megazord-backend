from typing import List, Optional

from ninja import Field, Schema
from ninja.orm import create_schema
from pydantic import BaseModel

from .models import Team

TeamSchema = create_schema(Team)


class SkillsAnalytics(Schema):
    skills: List[str]


class UserProfile(Schema):
    username: str = Field(..., min_length=1, max_length=30, required=True)
    email: str = Field(..., min_length=1, max_length=60, required=True)
    password: str = Field(..., min_length=6, required=True)
    is_organizator: bool
    age: Optional[int] = None
    city: Optional[str] = ""
    work_experience: Optional[int] = None


class ApplierSchema(Schema):
    app_id: int
    team: int
    vac: int
    who_responsed: int


class Account(Schema):
    id: int
    email: str
    name: str


class TeamById(Schema):
    id: int
    hackathon: int
    name: str
    creator: int
    team_members: List[Account]


class VacancySchema(BaseModel):
    id: int
    name: str
    keywords: List[str]


class AddUserToTeam(Schema):
    email: str


class VacancySchemaOut(Schema):
    id: int
    name: str
    keywords: List[str]


class TeamSchemaOut(Schema):
    id: int
    name: str
    vacancies: List[VacancySchema]


class TeamIn(Schema):
    name: str
    vacancies: List[VacancySchema]


class ApplyOut(Schema):
    applier_id: int
    vacancy_name: str


class Successful(Schema):
    success: str


class Error(Schema):
    details: str


class SentEmail(Schema):
    link: str


class UserData(Schema):
    id: int
    username: str = Field(..., min_length=1, max_length=30, required=True)
    email: str = Field(..., min_length=1, max_length=60, required=True)
    password: str = Field(..., min_length=6, required=True)
    is_organizator: bool
    age: Optional[int] = None
    city: Optional[str] = ""
    work_experience: Optional[int] = None
    keywords: List[str]
    bio: str


class UserDataVac(Schema):
    id: int
    username: str = Field(..., min_length=1, max_length=30, required=True)
    email: str = Field(..., min_length=1, max_length=60, required=True)
    password: str = Field(..., min_length=6, required=True)
    is_organizator: bool
    age: Optional[int] = None
    city: Optional[str] = ""
    work_experience: Optional[int] = None


class TeamData(Schema):
    id: int
    name: str
    team_members: List[UserDataVac]


class VacancyData(Schema):
    id: int
    name: str
    keywords: List[str]
    team: TeamData


class UserSuggesionForVacansionSchema(Schema):
    users: List[UserData]


class VacansionSuggesionForUserSchema(Schema):
    vacantions: List[VacancyData]


class AnalyticsSchema(Schema):
    procent: float


class AnalyticsDiffSchema(Schema):
    average_exp: float


class ParticipantOut(Schema):
    id: int
    email: str
    name: str
    role: str
