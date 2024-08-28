import uvicorn

from megazord import settings

uvicorn.run(
    app="megazord.asgi:application",
    reload=settings.RELOAD,
    host=settings.SERVER_HOST,
    port=settings.SERVER_PORT,
)
