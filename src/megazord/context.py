from contextvars import ContextVar

from megazord.api.requests import APIRequest

context_request: ContextVar[APIRequest] = ContextVar("context_request")
