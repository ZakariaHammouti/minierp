from fastapi import FastAPI

from src.controlling.api import router as controlling_router
from src.einkauf.api import router as einkauf_router

app = FastAPI(title="MiniERP")
app.include_router(einkauf_router)
app.include_router(controlling_router)