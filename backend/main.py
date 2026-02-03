"""FastAPI entrypoint for DK Sentinel."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException

from ai_services.config import LLMConfig
from ai_services.llm_safety_validator import LLMSafetyValidator
from ai_services.openai_provider import OpenAIProvider
from ai_services.semantic_auditor import BehavioralSemanticAuditor
from backend.routers import ai as ai_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _build_provider(config: LLMConfig) -> OpenAIProvider:
    """Construct the LLM provider based on config."""
    if config.provider != "openai":
        raise HTTPException(status_code=500, detail="Unsupported LLM provider.")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set.")
    return OpenAIProvider(api_key=api_key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan: init LLM clients on startup."""
    logger.info("Starting DK Sentinel API")
    config = LLMConfig()
    provider = _build_provider(config)
    app.state.semantic_auditor = BehavioralSemanticAuditor(provider=provider, config=config)
    app.state.nudge_validator = LLMSafetyValidator(provider=provider, config=config)
    logger.info("LLM clients initialized")
    yield
    logger.info("Shutting down DK Sentinel API")


app = FastAPI(
    title="DK Sentinel API",
    description="Responsible Gaming Analytics Intelligence System",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


app.include_router(ai_router.router, prefix="/api/ai", tags=["AI"])
