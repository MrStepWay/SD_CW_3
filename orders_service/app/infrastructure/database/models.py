import uuid
import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, text, Numeric, Enum as DBEnum, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID

class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"

class Base(DeclarativeBase):
    pass

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    description: Mapped[str]
    status: Mapped[OrderStatus] = mapped_column(
        DBEnum(OrderStatus, name="order_status_enum"),
        default=OrderStatus.NEW,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class OutboxMessage(Base):
    __tablename__ = "outbox_messages"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    topic: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSONB)
    is_published: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), index=True
    )
    __table_args__ = (
        Index(
            'ix_outbox_messages_unpublished_orders',
            'created_at',
            postgresql_where=is_published.is_(False)
        ),
    )