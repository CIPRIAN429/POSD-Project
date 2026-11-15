"""Private HTTP policy decision point. Only health is anonymous."""

import os
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException

from .models import AuthorizationRequest, Decision
from .policies import POLICY_VERSION, evaluate, policy_catalog


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.environ.get("POLICY_API_KEY", "").strip():
        raise RuntimeError("POLICY_API_KEY must be configured before starting the policy service.")
    yield


app = FastAPI(
    title="Access Granted Policy Service",
    version=POLICY_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.environ.get("POLICY_API_KEY", "")
    if not expected or not x_api_key or not secrets.compare_digest(
        x_api_key.encode("utf-8"), expected.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="A valid internal API key is required.")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": POLICY_VERSION}


@app.get("/policies", dependencies=[Depends(require_api_key)])
def policies() -> dict:
    return policy_catalog()


@app.post("/authorize", response_model=Decision, dependencies=[Depends(require_api_key)])
def authorize(request: AuthorizationRequest) -> Decision:
    return evaluate(request)
