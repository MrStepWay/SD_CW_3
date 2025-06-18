import logging
from decimal import Decimal
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.domain.models import Account, PaymentRequest, PaymentResult
from app.infrastructure.database.repository import (
    SQLAlchemyAccountRepository,
    SQLAlchemyInboxRepository,
    SQLAlchemyOutboxRepository,
)

log = logging.getLogger(__name__)

class PaymentService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create_account(self, user_id: int) -> Account:
        async with self.session_factory() as session:
            repo = SQLAlchemyAccountRepository(session)
            async with session.begin():
                if await repo.get_by_user_id(user_id):
                    raise ValueError("Account for this user already exists")
                account = await repo.create(user_id)
            return account

    async def deposit_to_account(self, user_id: int, amount: Decimal) -> Account:
        if amount <= Decimal(0):
            raise ValueError("Deposit amount must be positive")
        async with self.session_factory() as session:
            repo = SQLAlchemyAccountRepository(session)
            async with session.begin():
                account = await repo.deposit(user_id, amount)
            return account

    async def get_account_balance(self, user_id: int) -> Account:
        async with self.session_factory() as session:
            repo = SQLAlchemyAccountRepository(session)
            async with session.begin():
                account = await repo.get_by_user_id(user_id)
                if not account:
                    raise ValueError("Account not found")
            return account

    async def process_payment_request(self, payment_request: PaymentRequest) -> None:
        """
        Обрабатывает запрос на оплату в рамках одной транзакции.
        Создает новую сессию для каждой операции, обеспечивая изоляцию.
        """
        async with self.session_factory() as session:
            account_repo = SQLAlchemyAccountRepository(session)
            inbox_repo = SQLAlchemyInboxRepository(session)
            outbox_repo = SQLAlchemyOutboxRepository(session)

            async with session.begin():
                was_inserted = await inbox_repo.add(
                    message_id=payment_request.message_id,
                    topic="order.created",
                    payload=payment_request.model_dump(mode="json"),
                )
                if not was_inserted:
                    log.info(f"Duplicate payment request for message {payment_request.message_id}. Skipping.")
                    return

                success = await account_repo.withdraw(
                    payment_request.user_id, payment_request.amount
                )
                
                status, reason = ("SUCCESS", None) if success else ("FAIL", "Insufficient funds or account not found")

                result_payload = PaymentResult(
                    order_id=payment_request.order_id,
                    status=status,
                    reason=reason,
                ).model_dump(mode="json")
                result_payload['idempotency_key'] = str(payment_request.message_id)

                await outbox_repo.add(
                    topic="payment.processed",
                    payload=result_payload,
                )