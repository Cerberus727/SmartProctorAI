from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.models.database import engine, Base
from api.routes import auth, test, proctor, websockets
import logging

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Proctoring Platform", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(test.router, prefix="/api/test", tags=["test"])
app.include_router(proctor.router, prefix="/api/proctor", tags=["proctor"])
app.include_router(websockets.router, tags=["websockets"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend is running"}
