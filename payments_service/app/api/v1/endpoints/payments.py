from fastapi import APIRouter, HTTPException, status
from app.api.dependencies import PaymentServiceDep
from app.api.v1.schemas import AccountCreateRequest, DepositRequest, AccountResponse

router = APIRouter()

@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: AccountCreateRequest, service: PaymentServiceDep
):
    try:
        return await service.create_account(user_id=request.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.post("/accounts/deposit", response_model=AccountResponse)
async def deposit_to_account(
    request: DepositRequest, service: PaymentServiceDep
):
    try:
        return await service.deposit_to_account(
            user_id=request.user_id, amount=request.amount
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/accounts/{user_id}", response_model=AccountResponse)
async def get_account_balance(
    user_id: int, service: PaymentServiceDep
):
    try:
        return await service.get_account_balance(user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))