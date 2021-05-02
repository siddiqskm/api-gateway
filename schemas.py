from typing import Dict, List
from pydantic import (
    BaseModel, AnyUrl)


class Backend(BaseModel):
    backend_name: str
    path_prefix: str
    match_labels: Dict
    service_urls: List[AnyUrl] = []


class BackendServices(BaseModel):
    backends: List[Backend] = []


class DefaultResponse(BaseModel):
    body: str = 'This is not reachable'
    status_code: int = 403


class ConnectionNotAvailable(BaseModel):
    body: str = 'Connection down for the backend'
    status_code: int = 503


class BackendNotRunning(BaseModel):
    body: str = 'Backend available but no Service URLs discovered'
    status_code: int = 503


class ServiceResponse(BaseModel):
    body: dict
    status_code: int


class RequestsCount(BaseModel):
    success: int
    error: int


class LatencyMs(BaseModel):
    average: int
    p95: int
    p99: int


class StatsResponse(BaseModel):
    requests_count: RequestsCount
    latency_ms: LatencyMs
