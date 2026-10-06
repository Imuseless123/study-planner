from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import auth, consent, logs, subjects, assignments, dashboard

settings = get_settings()

app = FastAPI(
    title="Study Planner API - Tier 1",
    version="1.0.0",
    description="Web Application Layer: thu thap du lieu hanh vi hoc tap.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(consent.router)
app.include_router(logs.router)
app.include_router(subjects.router)
app.include_router(assignments.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "tier-1-web-app"}


@app.get("/")
def root():
    return {
        "service": "Study Planner - Tier 1",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
