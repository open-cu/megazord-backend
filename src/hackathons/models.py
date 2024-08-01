from django.db import models

from accounts.models import Account


class Hackathon(models.Model):
    creator = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="creator"
    )
    name = models.CharField(max_length=200, null=False)
    image_cover = models.ImageField(upload_to="hackathon_images/", null=True)
    description = models.TextField(null=False, default="описание хакатона")
    min_participants = models.IntegerField(null=True, default=3)
    max_participants = models.IntegerField(null=True, default=5)
    participants = models.ManyToManyField(
        Account, related_name="participants", null=True
    )
