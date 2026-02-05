"""FastAPI entrypoint for DK Sentinel."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from ai_services.config import LLMConfig
from ai_services.llm_safety_validator import LLMSafetyValidator
from ai_services.openai_provider import OpenAIProvider
from ai_services.semantic_auditor import BehavioralSemanticAuditor
from backend.db.duckdb_client import ensure_tables
from backend.routers import ai as ai_router
from backend.routers import cases as cases_router
from backend.routers import data as data_router
from backend.routers import interventions as interventions_router
from backend.routers import sql as sql_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()


def _build_provider(config: LLMConfig) -> OpenAIProvider | None:
    """Construct the LLM provider based on config.

    Args:
        config: LLM configuration settings.

    Returns:
        OpenAIProvider instance if configured; otherwise None.
    """
    if config.provider != "openai":
        logger.warning("Unsupported LLM provider '%s'", config.provider)
        return None
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; AI endpoints disabled")
        return None
    return OpenAIProvider(api_key=api_key)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup/shutdown behavior.

    Args:
        app: FastAPI application instance.

    Yields:
        None once startup completes.
    """
    logger.info("Starting DK Sentinel API")
    ensure_tables()

    config = LLMConfig()
    provider = _build_provider(config)
    app.state.llm_config = config
    app.state.llm_provider = provider
    app.state.semantic_auditor = (
        BehavioralSemanticAuditor(provider=provider, config=config) if provider else None
    )
    app.state.nudge_validator = (
        LLMSafetyValidator(provider=provider, config=config) if provider else None
    )
    app.state.analyst_name = os.getenv("ANALYST_NAME", "Colby Reichenbach")

    logger.info("Startup complete")
    yield
    logger.info("Shutting down DK Sentinel API")


app = FastAPI(
    title="DK Sentinel API",
    description="Responsible Gaming Analytics Intelligence System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Return service health status.

    Returns:
        Status payload with current timestamp.
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


app.include_router(ai_router.router, prefix="/api/ai", tags=["AI"])
app.include_router(interventions_router.router, prefix="/api/interventions", tags=["Interventions"])
app.include_router(cases_router.router, prefix="/api/cases", tags=["Cases"])
app.include_router(data_router.router, prefix="/api", tags=["Data"])
app.include_router(sql_router.router, prefix="/api", tags=["SQL"])
