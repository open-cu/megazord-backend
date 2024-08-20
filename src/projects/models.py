import uuid

from django.db import models

from resumes.models import Resume


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, blank=False)
    image_cover = models.ImageField(upload_to="project_images/")
    description = models.TextField(blank=False)
