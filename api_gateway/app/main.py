import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.services.proxy_client import proxy_client

log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("API Gateway starting up...")
    await proxy_client.start()
    yield
    log.info("API Gateway shutting down...")
    await proxy_client.stop()

app = FastAPI(
    title="API Gateway",
    description="Единая точка входа в систему.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}