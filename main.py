import asyncio
from fastapi import FastAPI
from app.database import init_db
from app.routes import user, video, audio, video_1

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await init_db() 

app.include_router(user.router)
app.include_router(video.router)
app.include_router(audio.router)
app.include_router(video_1.router)

@app.get("/")
async def root():
    return {"message": "FastAPI is running"}
