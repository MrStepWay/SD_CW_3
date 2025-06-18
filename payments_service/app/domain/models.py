import uuid
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class Account(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: int
    user_id: int
    balance: Decimal

class PaymentRequest(BaseModel):
    message_id: uuid.UUID
    order_id: int
    user_id: int
    amount: Decimal

class PaymentResult(BaseModel):
    order_id: int
    status: str
    reason: str | None = None