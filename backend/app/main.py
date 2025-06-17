from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongodb import mongodb
from contextlib import asynccontextmanager
from app.api import auth, chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongodb.connect()
    yield
    await mongodb.close()

app = FastAPI(title="YOURTravel", version="0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
# app.include_router(recommend.router, prefix="/recommend", tags=["Recommend"])
# app.include_router(graph.router, prefix="/graph", tags=["Graph"])

@app.get("/")
def root():
  return {"message": "Welcome to YOURTravel"}
