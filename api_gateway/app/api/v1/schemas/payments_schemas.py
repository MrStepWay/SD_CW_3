from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field, BeforeValidator

DecimalType = Annotated[
    Decimal,
    BeforeValidator(lambda v: Decimal(str(v))),
    Field(max_digits=18, decimal_places=2),
]

class AccountCreateRequest(BaseModel):
    user_id: int = Field(..., gt=0)

class DepositRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: DecimalType = Field(..., gt=Decimal(0))

class AccountResponse(BaseModel):
    id: int
    user_id: int
    balance: DecimalType