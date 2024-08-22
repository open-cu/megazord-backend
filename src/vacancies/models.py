import uuid

from django.db import models

from accounts.models import Account
from teams.models import Team
from vacancies.entities import ApplyEntity, VacancyEntity


class Vacancy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="vacancies")

    async def to_entity(self) -> VacancyEntity:
        return VacancyEntity(
            id=self.id,
            name=self.name,
            keywords=[keyword.text async for keyword in self.keywords.all()],
        )


class Keyword(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vacancy = models.ForeignKey(
        Vacancy, on_delete=models.CASCADE, related_name="keywords"
    )
    text = models.CharField(max_length=100, blank=False)


class Apply(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="applies")
    vac = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    who_responsed = models.ForeignKey(Account, on_delete=models.CASCADE)

    async def to_entity(self) -> ApplyEntity:
        return ApplyEntity(
            id=self.id,
            team=await self.team.to_entity(),
            vacancy=await self.vac.to_entity(),
            who_responsed=await self.who_responsed.to_entity(),
        )
