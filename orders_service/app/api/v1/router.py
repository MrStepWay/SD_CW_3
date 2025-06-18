from fastapi import APIRouter
from app.api.v1.endpoints import orders

api_router = APIRouter()
api_router.include_router(orders.router, prefix="/v1/orders", tags=["orders"])