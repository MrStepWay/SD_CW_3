import uuid
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import Order as DomainOrder
from app.domain.repositories import OrderRepository, OutboxRepository
from app.infrastructure.database.models import Order, OrderStatus, OutboxMessage

class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, amount: Decimal, description: str) -> DomainOrder:
        db_order = Order(
            user_id=user_id,
            amount=amount,
            description=description,
            status=OrderStatus.NEW
        )
        self.session.add(db_order)
        await self.session.flush()
        await self.session.refresh(db_order)
        return DomainOrder.model_validate(db_order)

    async def get_by_id(self, order_id: int, user_id: int) -> DomainOrder | None:
        stmt = select(Order).where(Order.id == order_id, Order.user_id == user_id)
        result = await self.session.execute(stmt)
        db_order = result.scalar_one_or_none()
        return DomainOrder.model_validate(db_order) if db_order else None

    async def list_by_user_id(self, user_id: int) -> list[DomainOrder]:
        stmt = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        result = await self.session.execute(stmt)
        orders = [DomainOrder.model_validate(o) for o in result.scalars().all()]
        return orders

    async def update_status(self, order_id: int, status: OrderStatus) -> bool:
        stmt = update(Order).where(Order.id == order_id).values(status=status)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

class SQLAlchemyOutboxRepository(OutboxRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, message_id: uuid.UUID, topic: str, payload: dict) -> None:
        db_outbox_msg = OutboxMessage(id=message_id, topic=topic, payload=payload)
        self.session.add(db_outbox_msg)