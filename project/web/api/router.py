from fastapi.routing import APIRouter

from project.web.api import monitoring
from project.web.api import users

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(users.router)
