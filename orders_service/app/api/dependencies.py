from typing import Annotated
from fastapi import Depends

from app.application.services import OrderService
from app.infrastructure.database.session import AsyncSessionLocal

def get_order_service() -> OrderService:
    return OrderService(session_factory=AsyncSessionLocal)

OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]