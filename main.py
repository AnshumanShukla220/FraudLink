import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError
from .database.store import db, publish, setup
from .ml.engine import analyze
from .routes.api import router
from .utils.ingest import parse_csv


@asynccontextmanager
async def lifespan(app):
    setup()
    if not db.state.find_one({"_id":"active"}):
        rows=parse_csv((Path(__file__).resolve().parents[1]/"datasets/demo.csv").read_bytes())
        data,model=analyze(rows)
        publish(data,model,"demo.csv",initial=True)
    yield


app=FastAPI(title="FraudLink Investigation API",version="1.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","http://localhost:5173,http://localhost:8080").split(","),
                   allow_methods=["GET","POST","PATCH"],allow_headers=["Content-Type"])
app.include_router(router)


@app.exception_handler(PyMongoError)
async def unavailable(request:Request,exc:PyMongoError):
    return JSONResponse(status_code=503,content={"detail":"Database unavailable. Retry shortly."})


@app.get("/health")
def health():
    db.command("ping")
    return {"status":"ready"}

