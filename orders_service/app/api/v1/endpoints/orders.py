from fastapi import APIRouter, HTTPException, status, Query
from app.api.dependencies import OrderServiceDep
from app.api.v1.schemas import OrderCreateRequest, OrderResponse

router = APIRouter()

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderCreateRequest, service: OrderServiceDep
):
    """
    Создает новый заказ.
    """
    order = await service.create_order(
        user_id=request.user_id,
        amount=request.amount,
        description=request.description
    )
    return order

@router.get("/", response_model=list[OrderResponse])
async def list_orders(
    *,
    user_id: int = Query(..., gt=0),
    service: OrderServiceDep
):
    """
    Возвращает список заказов для указанного пользователя.
    """
    orders = await service.list_orders_by_user(user_id)
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    *,
    user_id: int = Query(..., gt=0),
    service: OrderServiceDep
):
    """
    Возвращает информацию о конкретном заказе.
    """
    order = await service.get_order_by_id(order_id, user_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order