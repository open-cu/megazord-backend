import uvicorn

from megazord import settings

uvicorn.run(
    app="megazord.asgi:application",
    reload=settings.RELOAD,
    host="0.0.0.0",
    port=8000,
)
