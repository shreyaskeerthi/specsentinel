"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered spec-checker for commercial HVAC/Plumbing/Electrical contractors",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Root endpoint - health check."""
    return {
        "app": settings.APP_NAME,
        "status": "healthy",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Database initialization on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    from app.db.init_db import init_db
    init_db()
