# import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import UJSONResponse
from fastapi_pagination import add_pagination

from project.settings import settings
from project.web.api.router import api_router
from project.web.lifespan import lifespan_setup

# sentry_sdk.init(
#     dsn="x",
#     # Set traces_sample_rate to 1.0 to capture 100%
#     # of transactions for performance monitoring.
#     traces_sample_rate=0.3,
#     environment=settings.environment
# )


def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """
    app = FastAPI(
        title="order-inventory-platform",
        version="1",
        lifespan=lifespan_setup,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        default_response_class=UJSONResponse,
    )

    # Main router for the API.
    app.include_router(router=api_router, prefix="/api")
    add_pagination(app)
    return app
