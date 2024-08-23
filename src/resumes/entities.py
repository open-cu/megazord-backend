from dataclasses import dataclass


@dataclass
class ResumeEntity:
    id: str
    user_id: str
    hackathon_id: str

    role: str
    bio: str
    personal_website: str | None
    github: str | None
    hh: str | None
    telegram: str | None

    hard_skills: list[str]
    soft_skills: list[str]
