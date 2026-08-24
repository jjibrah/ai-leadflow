from fastapi import APIRouter
from app.api.routes import enquiries


api_router = APIRouter()
api_router.include_router(enquiries.router)