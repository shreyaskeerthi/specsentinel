"""API v1 router aggregating all endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, organizations, projects, documents, analysis, billing

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
