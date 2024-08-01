from django.db import models

from accounts.models import Account
from hackathons.models import Hackathon


class Team(models.Model):
    hackathon = models.ForeignKey(Hackathon, on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=200, blank=False)
    creator = models.ForeignKey(Account, on_delete=models.CASCADE)
    team_members = models.ManyToManyField(Account, related_name="team_members")


class Token(models.Model):
    token = models.CharField(max_length=200)
    is_active = models.BooleanField()
