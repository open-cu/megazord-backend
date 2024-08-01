from django.db.utils import IntegrityError
from django.http import Http404
from ninja import NinjaAPI
from ninja.errors import ValidationError

from accounts.api import router as accounts_router
from auth import InvalidToken, BadCredentials
from hackathons.api import hackathon_router, my_hackathon_router
from profiles.api import router as profiles_router
from projects.api import router as projects_router
from resumes.api import router as resumes_router
from teams.api import team_router

api = NinjaAPI(title="Team Search", description="API for team search")

api.add_router(
    prefix="/auth",
    router=accounts_router,
    tags=["Auth"]
)
api.add_router(
    prefix="/",
    router=profiles_router,
    tags=["Profile"]
)
api.add_router(
    prefix="/hackathons",
    router=hackathon_router,
    tags=["Hackathons"]
)
api.add_router(
    prefix="/myhackathons",
    router=my_hackathon_router,
    tags=["My hackathons"]
)
api.add_router(
    prefix="/teams",
    router=team_router,
    tags=["Teams"]
)
api.add_router(
    prefix="/projects",
    router=projects_router,
    tags=["Projects"]
)
api.add_router(
    prefix="/resumes",
    router=resumes_router,
    tags=["Resumes"]
)


@api.exception_handler(IntegrityError)
def integrity_error(request, exc):
    return api.create_response(
        request, {"details": f"Already exist: {exc}"}, status=409
    )


@api.exception_handler(ValueError)
def value_error(request, exc):
    return api.create_response(
        request, {"details": f"Value is not valid: {exc}"}, status=422
    )


@api.exception_handler(InvalidToken)
def invalid_token(request, exc):
    return api.create_response(
        request, {"details": "Provided token is not valid"}, status=401
    )


@api.exception_handler(BadCredentials)
def bad_credentials(request, exc):
    return api.create_response(
        request, {"details": "Invalid login credentials"}, status=401
    )

@api.exception_handler(Http404)
def handle_404(request, exc):
    return api.create_response(
        request, {"details": "Not found or data is not correct"}, status=404
    )


@api.exception_handler(ValidationError)
def handle_validation_error(request, exc):
    return api.create_response(
        request, {"details": f"Some data is not valid: {exc}"}, status=422
    )
