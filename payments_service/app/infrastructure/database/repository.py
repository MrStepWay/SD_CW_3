import uuid
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import Account as DomainAccount
from app.domain.repositories import AccountRepository, InboxRepository, OutboxRepository
from app.infrastructure.database.models import Account, InboxMessage, OutboxMessage

class SQLAlchemyAccountRepository(AccountRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int) -> DomainAccount:
        db_account = Account(user_id=user_id, balance=Decimal("0.00"))
        self.session.add(db_account)
        await self.session.flush()
        await self.session.refresh(db_account)
        return DomainAccount.model_validate(db_account)

    async def get_by_user_id(self, user_id: int) -> DomainAccount | None:
        stmt = select(Account).where(Account.user_id == user_id)
        result = await self.session.execute(stmt)
        db_account = result.scalar_one_or_none()
        return DomainAccount.model_validate(db_account) if db_account else None

    async def deposit(self, user_id: int, amount: Decimal) -> DomainAccount:
        stmt = select(Account).where(Account.user_id == user_id).with_for_update()
        account = await self.session.scalar(stmt)
        if not account:
            raise ValueError("Account not found")

        account.balance += amount
        await self.session.flush()
        await self.session.refresh(account)

        return DomainAccount.model_validate(account)

    async def withdraw(self, user_id: int, amount: Decimal) -> bool:
        stmt = select(Account).where(Account.user_id == user_id).with_for_update()
        account = await self.session.scalar(stmt)

        if not account or account.balance < amount:
            return False

        account.balance -= amount
        await self.session.flush()
        return True

class SQLAlchemyInboxRepository(InboxRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, message_id: uuid.UUID, topic: str, payload: dict) -> bool:
        msg = InboxMessage(id=message_id, topic=topic, payload=payload)
        self.session.add(msg)
        try:
            await self.session.flush()
            return True
        except IntegrityError:
            await self.session.rollback()
            return False

class SQLAlchemyOutboxRepository(OutboxRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, topic: str, payload: dict) -> None:
        db_outbox_msg = OutboxMessage(topic=topic, payload=payload)
        self.session.add(db_outbox_msg)