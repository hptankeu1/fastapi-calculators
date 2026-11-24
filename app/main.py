from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app import models  # noqa: F401  (registers models on Base.metadata)
from app.database import Base, engine
from app.routers import calculations, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FastAPI Calculator",
    version="1.0.0",
    description=(
        "User registration/login (bcrypt + JWT) and calculation BREAD.\n\n"
        "1. `POST /users/register`  2. `POST /users/login` and copy `access_token`  "
        "3. Click **Authorize** and paste the token  4. Use the `/calculations` endpoints."
    ),
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(calculations.router)


@app.get("/", tags=["health"])
def root():
    return {"message": "FastAPI Calculator is running", "docs": "/docs"}


@app.get("/health", tags=["health"])
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
