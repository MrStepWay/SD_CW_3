from fastapi import APIRouter, Request, Query
from app.core.config import settings
from app.services.proxy_client import proxy_client
from app.api.v1.schemas.orders_schemas import (
    OrderCreateRequest,
    OrderResponse,
)

router = APIRouter()
BASE_URL = settings.ORDERS_SERVICE_URL

@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(request: Request, _: OrderCreateRequest):
    return await proxy_client.forward_request(BASE_URL, request)

@router.get("/", response_model=list[OrderResponse])
async def list_orders(request: Request, user_id: int = Query(..., gt=0)):
    return await proxy_client.forward_request(BASE_URL, request)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(request: Request, order_id: int, user_id: int = Query(..., gt=0)):
    return await proxy_client.forward_request(BASE_URL, request)