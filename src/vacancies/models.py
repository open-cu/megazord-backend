import uuid

from django.db import models

from accounts.models import Account
from teams.models import Team


class Vacancy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)


class Keyword(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    text = models.CharField(max_length=100, blank=False)


class Apply(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    vac = models.ForeignKey(Vacancy, on_delete=models.CASCADE)
    who_responsed = models.ForeignKey(Account, on_delete=models.CASCADE)
