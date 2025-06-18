import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from app.domain.models import Account

# "Интерфейсы" репозиториев
class AccountRepository(ABC):
    @abstractmethod
    async def create(self, user_id: int) -> Account: ...
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Account | None: ...
    @abstractmethod
    async def deposit(self, user_id: int, amount: Decimal) -> Account: ...
    @abstractmethod
    async def withdraw(self, user_id: int, amount: Decimal) -> bool: ...

class InboxRepository(ABC):
    @abstractmethod
    async def add(self, message_id: uuid.UUID, topic: str, payload: dict) -> bool:
        ...

class OutboxRepository(ABC):
    @abstractmethod
    async def add(self, topic: str, payload: dict) -> None: ...