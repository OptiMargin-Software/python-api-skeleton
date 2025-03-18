import time
from datetime import date

import prometheus_client
from fastapi import Depends, FastAPI, Query, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from requests import get
from starlette_exporter import PrometheusMiddleware, handle_metrics
from app.utils import validate_token, JWKS_URL


class ApiResponse(BaseModel):
    message: str | dict


security = HTTPBearer()
app = FastAPI()


health_check_processing_time = prometheus_client.Histogram(
    "health_check_processing_time_seconds",
    "Time taken to process health_check endpoint",
    ["method", "endpoint"],
)

health_check_requests_counter = prometheus_client.Counter(
    "health_check_requests_total",
    "Total number of requests to the health_check endpoint",
    ["method", "endpoint"],
)

hello_world_processing_time = prometheus_client.Histogram(
    "hello_world_processing_time_seconds",
    "Time taken to process the endpoint",
    ["method", "endpoint"],
)

hello_world_requests_counter = prometheus_client.Counter(
    "hello_world_requests_total",
    "Total number of requests to the hello_world endpoint",
    ["method", "endpoint"],
)


app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

start_time = time.time()


@app.get("/health/")
async def health_check(request: Request) -> ApiResponse:
    """Health check endpoint."""
    health_check_requests_counter.labels(
        method=request.method, endpoint=request.url.path
    ).inc()
    checks = {}

    with health_check_processing_time.labels(
        method=request.method, endpoint=request.url.path
    ).time():
        try:
            jwks = get(JWKS_URL)

            if jwks.status_code == 200:
                checks["jwks"] = "healthy"
            else:
                checks["jwks"] = "unhealthy"

        except Exception as e:
            checks["jwks"] = "unhealthy"

        return ApiResponse(message=checks)


@app.get(
    "/",
    dependencies=[Depends(validate_token)],
)
async def hello_world(
    request: Request,
    name: str = Query("World", description="Your name."),
) -> ApiResponse:
    """Hello world endpoint."""
    hello_world_requests_counter.labels(
        method=request.method, endpoint=request.url.path
    ).inc()

    with hello_world_processing_time.labels(
        method=request.method, endpoint=request.url.path
    ).time():
        return {"message": f"Hello, " + name + f"! The current date is {date.today()}."}
