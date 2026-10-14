"""Risk Indicator service — FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .schemas import HealthResponse

app = FastAPI(
    title="Study Planner — Workload Risk Indicator",
    version="1.0.0",
    description=(
        "Rule-based workload risk scoring service. "
        "This service does NOT diagnose burnout or any medical/psychological "
        "condition. It only reflects self-reported workload stress levels "
        "to support time management."
    ),
)

# CORS — allow Tier 1 backend and frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # frontend
        "http://localhost:8000",  # tier-1 backend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["default"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="risk-indicator",
        version="1.0.0",
    )


@app.get("/", tags=["default"])
def root():
    return {
        "service": "Study Planner — Workload Risk Indicator",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoint": "POST /api/risk/score",
    }
