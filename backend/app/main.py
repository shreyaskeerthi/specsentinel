"""FastAPI application — SpecSentinel v2."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import init_db
from app.api.routes import router

os.makedirs(settings.FILE_STORAGE_PATH, exist_ok=True)

app = FastAPI(
    title="SpecSentinel",
    description="AI Bid Risk Intelligence for MEP Contractors",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"app": "SpecSentinel", "status": "healthy", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
