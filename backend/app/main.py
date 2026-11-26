from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import router
from app.config import ALLOWED_ORIGINS
from app.database import initialize_database


@asynccontextmanager
async def lifespan(application):
    initialize_database()
    yield


app = FastAPI(
    title="ReVithalize Fleet Intelligence Engine (RFIE)",
    description="Fleet scoring, recommendations and risk alerts for the RFIE dashboard.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=500, content={"detail": "A database error occurred."})


@app.get("/")
def root():
    return {"name": app.title, "documentation": "/docs", "health": "/api/health"}


app.include_router(router)
