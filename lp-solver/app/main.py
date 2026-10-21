"""LP Optimization Engine — FastAPI service."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .schemas import HealthResponse

app = FastAPI(
    title="Study Planner — LP Optimization Engine",
    version="1.0.0",
    description=(
        "MILP-based study schedule optimizer. Uses PuLP with CBC solver. "
        "Objective: maximize weighted study effectiveness with diminishing returns, "
        "subject to behavioral constraints and risk-adjusted daily cap."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["default"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="lp-solver", version="1.0.0")


@app.get("/", tags=["default"])
def root():
    return {
        "service": "Study Planner — LP Optimization Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoint": "POST /api/schedule/generate",
    }
