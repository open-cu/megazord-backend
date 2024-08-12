from django.contrib import admin

from resumes.models import Resume


# Register your models here.

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("user", "hackathon")
