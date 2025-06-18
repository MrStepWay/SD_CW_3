from fastapi import APIRouter, Request
from app.core.config import settings
from app.services.proxy_client import proxy_client
from app.api.v1.schemas.payments_schemas import (
    AccountCreateRequest,
    DepositRequest,
    AccountResponse,
)

router = APIRouter()
BASE_URL = settings.PAYMENTS_SERVICE_URL

@router.post("/accounts", response_model=AccountResponse, status_code=201)
async def create_account(request: Request, _: AccountCreateRequest):
    return await proxy_client.forward_request(BASE_URL, request)

@router.post("/accounts/deposit", response_model=AccountResponse)
async def deposit_to_account(request: Request, _: DepositRequest):
    return await proxy_client.forward_request(BASE_URL, request)

@router.get("/accounts/{user_id}", response_model=AccountResponse)
async def get_account_balance(request: Request, user_id: int):
    return await proxy_client.forward_request(BASE_URL, request)