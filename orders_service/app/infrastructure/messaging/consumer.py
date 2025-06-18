import asyncio
import json
import uuid
import logging
from typing import Callable, Coroutine, Any

import aio_pika
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractRobustConnection,
    AbstractChannel,
    AbstractQueue,
)

from app.core.config import RabbitMQSettings
from app.domain.models import OrderStatusUpdate

log = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(
        self,
        settings: RabbitMQSettings,
        on_message_callback: Callable[[OrderStatusUpdate], Coroutine[Any, Any, None]],
    ):
        self.settings = settings
        self.on_message_callback = on_message_callback
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None
        self._queue: AbstractQueue | None = None
        self._consuming_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(self.settings.url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        exchange = await self._channel.declare_exchange(
            "store_exchange", aio_pika.ExchangeType.TOPIC, durable=True
        )
        
        self._queue = await self._channel.declare_queue(
            "order_status_updates_queue", durable=True
        )
        await self._queue.bind(exchange, routing_key="payment.processed")

        log.info("Consumer for order status updates started.")
        self._consuming_task = asyncio.create_task(
            self._queue.consume(self._process_message)
        )

    async def stop(self) -> None:
        log.info("Stopping RabbitMQ consumer...")
        if self._consuming_task and not self._consuming_task.done():
            self._consuming_task.cancel()
            try:
                await self._consuming_task
            except asyncio.CancelledError:
                log.info("Consuming task successfully cancelled.")

        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            log.info("RabbitMQ connection closed.")
        
        log.info("RabbitMQ consumer stopped.")

    async def _process_message(self, message: AbstractIncomingMessage) -> None:
        try:
            body = json.loads(message.body.decode())
            update_data = OrderStatusUpdate(
                order_id=body["order_id"],
                status=body["status"],
                idempotency_key=uuid.UUID(body["idempotency_key"])
            )
            await self.on_message_callback(update_data)
            await message.ack()
        except Exception:
            log.exception("Failed to process order status update. Rejecting.")
            await message.reject(requeue=False)