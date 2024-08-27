from megazord.api.requests import APIRequest
from megazord.context import context_request


class ContextRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: APIRequest) -> None:
        context_request.set(request)

        response = self.get_response(request)

        return response
