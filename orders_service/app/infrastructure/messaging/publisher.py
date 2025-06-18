import asyncio
import json
import logging
from typing import Callable

import aio_pika
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import RabbitMQSettings
from app.infrastructure.database.models import OutboxMessage

log = logging.getLogger(__name__)
POLL_INTERVAL = 2.0

class OutboxPublisher:
    def __init__(
        self,
        db_session_factory: async_sessionmaker[AsyncSession],
        rabbitmq_settings: RabbitMQSettings,
    ):
        self.db_session_factory = db_session_factory
        self.rabbitmq_settings = rabbitmq_settings
        self._stopped = asyncio.Event()
        self.connection: aio_pika.abc.AbstractRobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None
        self.exchange: aio_pika.abc.AbstractExchange | None = None

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
    async def _get_connection(self):
        return await aio_pika.connect_robust(self.rabbitmq_settings.url)

    async def _setup(self):
        self.connection = await self._get_connection()
        self.channel = await self.connection.channel(publisher_confirms=True)
        self.exchange = await self.channel.declare_exchange(
            "store_exchange", aio_pika.ExchangeType.TOPIC, durable=True
        )
        log.info("Outbox Publisher connection and channel set up.")

    async def run(self) -> None:
        await self._setup()
        log.info("Outbox Publisher started.")
        while not self._stopped.is_set():
            try:
                await self._publish_pending_messages()
            except Exception as e:
                log.error(f"Outbox publisher cycle failed: {e}", exc_info=True)
                if not self.connection or self.connection.is_closed:
                    try:
                        await self._setup()
                    except Exception as setup_exc:
                        log.error(f"Failed to re-setup publisher connection: {setup_exc}")
                await asyncio.sleep(POLL_INTERVAL * 2)
            await asyncio.sleep(POLL_INTERVAL)

    async def stop(self) -> None:
        self._stopped.set()
        log.info("Outbox Publisher stopping.")
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def _publish_pending_messages(self) -> None:
        if self.exchange is None:
            raise RuntimeError("Exchange is not initialized in OutboxPublisher.")

        async with self.db_session_factory() as session:
            async with session.begin():
                stmt = (
                    select(OutboxMessage)
                    .where(OutboxMessage.is_published.is_(False))
                    .order_by(OutboxMessage.created_at)
                    .limit(100)
                    .with_for_update(skip_locked=True)
                )
                messages_to_publish = (await session.scalars(stmt)).all()

                if not messages_to_publish:
                    return

                for msg in messages_to_publish:
                    try:
                        await self.exchange.publish(
                            aio_pika.Message(
                                body=json.dumps(msg.payload, default=str).encode(),
                                headers={"message_id": str(msg.id)},
                                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                            ),
                            routing_key=msg.topic,
                        )
                        msg.is_published = True
                    except Exception:
                        log.exception(f"Failed to publish message {msg.id}. "
                                      "Transaction will be rolled back, and it will be retried.")
                        raise