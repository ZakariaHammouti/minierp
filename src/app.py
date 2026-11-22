from fastapi import FastAPI

from src.einkauf.api import router as einkauf_router

app = FastAPI(title="MiniERP")
app.include_router(einkauf_router)