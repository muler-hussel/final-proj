from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.mongodb import mongodb
from contextlib import asynccontextmanager
from app.api import auth, chat, recommend, survey
from app.utils.async_listener import RedisExpiredListener
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
  await mongodb.connect()
  listener = RedisExpiredListener("redis://localhost:6379/0")
  task = asyncio.create_task(listener.listen())

  yield

  task.cancel()
  try:
    await task
  except asyncio.CancelledError:
    print("Redis listener task cancelled")
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
app.include_router(recommend.router)
app.include_router(survey.router)

@app.get("/")
def root():
  return {"message": "Welcome to YOURTravel"}
