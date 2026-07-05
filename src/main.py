from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import close_db, init_db
from src.routers import auth, categories, share_links, statuses, tasks, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Task Management API",
    description="FastAPI + SQLAlchemy Task Management Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(statuses.router, prefix="/api/v1")
app.include_router(share_links.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
