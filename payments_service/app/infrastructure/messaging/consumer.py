import asyncio
import json
import uuid
import logging
from decimal import Decimal
from typing import Callable, Coroutine, Any

import aio_pika
from aio_pika.abc import (
    AbstractIncomingMessage,
    AbstractRobustConnection,
    AbstractChannel,
    AbstractQueue,
)

from app.core.config import RabbitMQSettings
from app.domain.models import PaymentRequest

log = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(
        self,
        settings: RabbitMQSettings,
        on_message_callback: Callable[[PaymentRequest], Coroutine[Any, Any, None]],
    ):
        self.settings = settings
        self.on_message_callback = on_message_callback

        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None
        self._queue: AbstractQueue | None = None
        self._consuming_task: asyncio.Task | None = None

    async def start(self) -> None:
        """
        Устанавливает соединение, настраивает канал и очередь,
        и запускает процесс потребления сообщений в фоновой задаче.
        """
        self._connection = await aio_pika.connect_robust(self.settings.url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        exchange = await self._channel.declare_exchange(
            "store_exchange", aio_pika.ExchangeType.TOPIC, durable=True
        )
        
        dlx_exchange = await self._channel.declare_exchange(
            "dlx_exchange", aio_pika.ExchangeType.FANOUT, durable=True
        )
        dlq_queue = await self._channel.declare_queue(
            "payment_requests_dlq", durable=True
        )
        await dlq_queue.bind(dlx_exchange, "")

        self._queue = await self._channel.declare_queue(
            "payment_requests_queue",
            durable=True,
            arguments={"x-dead-letter-exchange": "dlx_exchange"},
        )
        await self._queue.bind(exchange, routing_key="order.created")

        log.info("Consumer started. Waiting for messages.")

        # Запускаем consume как управляемую фоновую задачу
        self._consuming_task = asyncio.create_task(
            self._queue.consume(self._process_message)
        )

    async def stop(self) -> None:
        """
        Корректно останавливает потребителя: отменяет задачу потребления
        и закрывает соединение с RabbitMQ.
        """
        log.info("Stopping RabbitMQ consumer...")
        if self._consuming_task and not self._consuming_task.done():
            # Отменяем задачу, которая слушает очередь
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
        """
        Обрабатывает входящее сообщение.
        Подтверждение (ACK) отправляется только после успешной обработки.
        При любой ошибке сообщение реджектится.
        """
        try:
            body = json.loads(message.body.decode())
            msg_id_hdr = message.headers.get("message_id")

            if not isinstance(msg_id_hdr, str):
                raise ValueError("Header 'message_id' is missing or not a string")

            payment_request = PaymentRequest(
                message_id=uuid.UUID(msg_id_hdr),
                order_id=body["order_id"],
                user_id=body["user_id"],
                amount=Decimal(str(body["amount"])),
            )
            
            # Вся бизнес-логика, включая коммит в БД, происходит здесь.
            await self.on_message_callback(payment_request)
            
            # Подтверждаем сообщение только после успешного выполнения колбэка
            await message.ack()
            log.info(f"Successfully processed and ACKed message {msg_id_hdr}")

        except Exception:
            log.exception(f"Failed to process message. Rejecting to DLQ.")
            # Отклоняем сообщение, чтобы оно ушло в DLQ и не было потеряно
            await message.reject(requeue=False)