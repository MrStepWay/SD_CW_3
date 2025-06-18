import uuid
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.infrastructure.database.models import OrderStatus

class Order(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: int
    user_id: int
    amount: Decimal
    description: str
    status: OrderStatus

class OrderStatusUpdate(BaseModel):
    order_id: int
    status: str
    idempotency_key: uuid.UUID