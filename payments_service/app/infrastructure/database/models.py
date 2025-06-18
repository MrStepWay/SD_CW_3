import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, text, Numeric, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, UUID

class Base(DeclarativeBase):
    pass

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(unique=True, index=True)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), server_default=text("0.00"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

class InboxMessage(Base):
    __tablename__ = "inbox_messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    topic: Mapped[str] = mapped_column(index=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    processed_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), index=True
    )

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
            'ix_outbox_messages_unpublished',
            'created_at',
            postgresql_where=is_published.is_(False)
        ),
    )