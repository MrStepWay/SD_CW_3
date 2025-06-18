import httpx
from fastapi import Request
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTask

class ProxyClient:
    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def start(self):
        timeout = httpx.Timeout(10.0, connect=5.0)
        self.client = httpx.AsyncClient(timeout=timeout)

    async def stop(self):
        if self.client:
            await self.client.aclose()

    async def forward_request(
        self,
        base_url: str,
        request: Request,
    ) -> StreamingResponse:
        if not self.client:
            raise RuntimeError("ProxyClient not started")
        
        target_url = httpx.URL(
            url=f"{base_url}{request.url.path}",
            query=request.url.query.encode("utf-8")
        )
        
        headers = {
            key: value for key, value in request.headers.items()
            if key.lower() not in ("host", "user-agent", "accept-encoding")
        }
        
        rp_req = self.client.build_request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=await request.body(),
        )
        
        rp_resp = await self.client.send(rp_req, stream=True)

        return StreamingResponse(
            rp_resp.aiter_raw(),
            status_code=rp_resp.status_code,
            headers=rp_resp.headers,
            background=BackgroundTask(rp_resp.aclose),
        )

proxy_client = ProxyClient()