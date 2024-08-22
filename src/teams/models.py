import uuid

from django.db import models

from accounts.models import Account
from hackathons.models import Hackathon
from teams.entities import TeamEntity


class Team(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )  # Добавлено UUID поле
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=200, blank=False)
    creator = models.ForeignKey(Account, on_delete=models.CASCADE)
    team_members = models.ManyToManyField(Account, related_name="team_members")

    async def to_entity(self) -> TeamEntity:
        return TeamEntity(
            id=self.id,
            hackathon_id=str(self.hackathon_id),
            name=self.name,
            creator_id=str(self.creator_id),
            team_members=[
                await member.to_entity() async for member in self.team_members.all()
            ],
        )


class Token(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )  # Добавлено UUID поле
    token = models.CharField(max_length=200)
    is_active = models.BooleanField()
