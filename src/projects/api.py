import uuid

from django.shortcuts import get_object_or_404
from ninja import File, Router, UploadedFile

from megazord.api.auth import AuthBearer
from megazord.api.requests import APIRequest
from megazord.schemas import ErrorSchema
from resumes.models import Resume

from .models import Project as ProjectModel
from .schemas import ProjectSchema

router = Router(auth=AuthBearer())


@router.post(
    path="/create", response={201: ProjectSchema, 401: ErrorSchema, 422: ErrorSchema}
)
def create_project(
    request: APIRequest, project: ProjectSchema, image_cover: UploadedFile = File(...)
) -> tuple[int, ProjectSchema]:
    resume = get_object_or_404(Resume, id=project.resume_id)
    new_project = ProjectModel.objects.create(
        name=project.name, description=project.description, resume=resume
    )
    new_project.image_cover.save(image_cover.name, image_cover)
    return 201, new_project


@router.get(path="/", response={200: list[ProjectSchema], 401: ErrorSchema})
def get_projects(
    request: APIRequest, resume_id: uuid.UUID
) -> tuple[int, list[ProjectSchema]]:
    resume = get_object_or_404(Resume, id=resume_id)
    projects = ProjectModel.objects.filter(resume=resume)
    return 200, projects
