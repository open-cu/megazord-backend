from dataclasses import dataclass

from teams.entities import TeamEntity


@dataclass
class VacancyEntity:
    id: str
    name: str
    keywords: list[str]
    team: TeamEntity


@dataclass
class ApplyEntity:
    id: str
    team_id: str
    vacancy_id: str
    who_response_id: str
