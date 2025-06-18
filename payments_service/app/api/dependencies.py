from typing import Annotated
from fastapi import Depends

from app.application.services import PaymentService
from app.infrastructure.database.session import AsyncSessionLocal

def get_payment_service() -> PaymentService:
    """
    Создает экземпляр PaymentService, передавая ему фабрику сессий.
    Сервис будет сам создавать сессии по мере необходимости.
    """
    return PaymentService(session_factory=AsyncSessionLocal)

PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]