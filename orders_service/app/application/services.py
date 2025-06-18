import logging
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.domain.models import Order, OrderStatusUpdate
from app.infrastructure.database.models import OrderStatus
from app.infrastructure.database.repository import (
    SQLAlchemyOrderRepository,
    SQLAlchemyOutboxRepository,
)

log = logging.getLogger(__name__)

class OrderService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create_order(
        self, user_id: int, amount: Decimal, description: str
    ) -> Order:
        async with self.session_factory() as session:
            order_repo = SQLAlchemyOrderRepository(session)
            outbox_repo = SQLAlchemyOutboxRepository(session)
            
            async with session.begin():
                order = await order_repo.create(user_id, amount, description)
                
                message_id = uuid.uuid4()
                payload = {
                    "order_id": order.id,
                    "user_id": user_id,
                    "amount": str(amount),
                }
                await outbox_repo.add(
                    message_id=message_id,
                    topic="order.created",
                    payload=payload
                )
        return order

    async def update_order_status(self, update_data: OrderStatusUpdate) -> None:
        async with self.session_factory() as session:
            order_repo = SQLAlchemyOrderRepository(session)
            async with session.begin():
                new_status = (
                    OrderStatus.FINISHED if update_data.status == "SUCCESS"
                    else OrderStatus.CANCELLED
                )
                updated = await order_repo.update_status(update_data.order_id, new_status)
                if updated:
                    log.info(f"Order {update_data.order_id} status updated to {new_status.name}")
                else:
                    log.warning(f"Order {update_data.order_id} not found for status update.")

    async def get_order_by_id(self, order_id: int, user_id: int) -> Order | None:
        async with self.session_factory() as session:
            repo = SQLAlchemyOrderRepository(session)
            async with session.begin():
                return await repo.get_by_id(order_id, user_id)

    async def list_orders_by_user(self, user_id: int) -> list[Order]:
        async with self.session_factory() as session:
            repo = SQLAlchemyOrderRepository(session)
            async with session.begin():
                return await repo.list_by_user_id(user_id)