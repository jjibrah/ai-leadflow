from fastapi import APIRouter
from app.api.routes import enquiries, webhooks


api_router = APIRouter()
api_router.include_router(enquiries.router)
api_router.include_router(webhooks.router)