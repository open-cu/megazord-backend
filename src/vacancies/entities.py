from dataclasses import dataclass

from accounts.entities import AccountEntity
from teams.entities import TeamEntity


@dataclass
class VacancyEntity:
    id: str
    name: str
    keywords: list[str]


@dataclass
class ApplyEntity:
    id: str
    team: TeamEntity
    vacancy: VacancyEntity
    who_responsed: AccountEntity
