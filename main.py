import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.router.package import router as package_router
from app.config import settings
from app.database import sessionmanager
from os import environ

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if settings.log_level == "DEBUG" else logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan, title=settings.project_name, docs_url="/api/docs")


@app.get("/")
async def root():
    return {"message": "OBS SCM live!"}


# Routers
app.include_router(package_router)


if __name__ == "__main__":
    port = environ.get("OBS_SCM_CACHE_PORT", 8000)
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=int(port))
