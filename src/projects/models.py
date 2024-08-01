from django.db import models

from resumes.models import Resume


class Project(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, blank=False)
    image_cover = models.ImageField(upload_to="project_images/")
    description = models.TextField(blank=False)
