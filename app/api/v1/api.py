from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import chatbots
from app.api.v1.endpoints import webhooks
from app.api.v1.endpoints import chat
from app.api.v1.endpoints import documents
from app.api.v1.endpoints import notebooks
from app.api.v1.endpoints import credit_manager
from app.api.v1.endpoints import chatbot_manager
from app.api.v1.endpoints import reminders
from app.api.v1.endpoints import line
from app.api.v1.endpoints import revenuecat

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(chatbots.router)
api_router.include_router(webhooks.router)
api_router.include_router(chat.router)
api_router.include_router(documents.router)
api_router.include_router(notebooks.router)
api_router.include_router(credit_manager.router)
api_router.include_router(chatbot_manager.router)
api_router.include_router(reminders.router)
api_router.include_router(line.router)
api_router.include_router(revenuecat.router)