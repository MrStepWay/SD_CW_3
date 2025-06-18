import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type,
    RetryCallState
)

from app.api.v1.router import api_router
from app.core.config import settings
from app.domain.models import PaymentRequest
from app.infrastructure.database.models import Base
from app.infrastructure.database.session import async_engine, AsyncSessionLocal
from app.infrastructure.messaging.consumer import RabbitMQConsumer
from app.infrastructure.messaging.publisher import OutboxPublisher
from app.application.services import PaymentService

log = logging.getLogger(__name__)

publisher: OutboxPublisher | None = None
consumer: RabbitMQConsumer | None = None

def _log_on_retry(retry_state: RetryCallState):
    """Логгирует информацию при повторной попытке."""
    if retry_state.outcome and retry_state.outcome.failed:
        log.error(
            f"Retrying payment processing, attempt {retry_state.attempt_number} failed.",
            exc_info=retry_state.outcome.exception()
        )

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(OperationalError),
    retry_error_callback=_log_on_retry
)
async def handle_payment_request(payment_request: PaymentRequest):
    """
    Создает сервис и обрабатывает запрос.
    Эта функция будет вызываться повторно в случае временных сбоев.
    """
    service = PaymentService(session_factory=AsyncSessionLocal)
    await service.process_payment_request(payment_request)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global publisher, consumer
    log.info("Payments Service starting up...")
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    publisher = OutboxPublisher(AsyncSessionLocal, settings.rabbitmq)
    consumer = RabbitMQConsumer(settings.rabbitmq, handle_payment_request)
    
    publisher_task = asyncio.create_task(publisher.run())
    consumer_task = asyncio.create_task(consumer.start())

    yield

    log.info("Payments Service shutting down...")
    if publisher:
        await publisher.stop()
    if consumer:
        await consumer.stop()
    
    await asyncio.gather(publisher_task, consumer_task, return_exceptions=True)
    log.info("Background tasks finished.")

app = FastAPI(
    title="Payments Service",
    description="Сервис для управления счетами и проведения оплат.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}