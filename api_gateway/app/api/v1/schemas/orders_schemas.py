import enum
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field, BeforeValidator

class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"

DecimalType = Annotated[
    Decimal,
    BeforeValidator(lambda v: Decimal(str(v))),
    Field(max_digits=18, decimal_places=2),
]

class OrderCreateRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: DecimalType
    description: str = Field(..., min_length=1, max_length=255)

class OrderResponse(BaseModel):
    id: int
    user_id: int
    amount: DecimalType
    description: str
    status: OrderStatus