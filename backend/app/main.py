from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, recommend, graph

app = FastAPI(title="YOURTravel", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(recommend.router, prefix="/recommend", tags=["Recommend"])
app.include_router(graph.router, prefix="/graph", tags=["Graph"])

@app.get("/")
def root():
    return {"message": "Welcome to YOURTravel"}
