import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from app.domain.models import Order
from app.infrastructure.database.models import OrderStatus

# "Интерфейсы" репозиториев
class OrderRepository(ABC):
    @abstractmethod
    async def create(self, user_id: int, amount: Decimal, description: str) -> Order:
        ...

    @abstractmethod
    async def get_by_id(self, order_id: int, user_id: int) -> Order | None:
        ...

    @abstractmethod
    async def list_by_user_id(self, user_id: int) -> list[Order]:
        ...

    @abstractmethod
    async def update_status(self, order_id: int, status: OrderStatus) -> bool:
        ...

class OutboxRepository(ABC):
    @abstractmethod
    async def add(self, message_id: uuid.UUID, topic: str, payload: dict) -> None:
        ...