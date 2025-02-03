from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import video

app = FastAPI(
    title="Video Generation API",
    description="""
    API for generating videos from images using RunwayML.
    
    Features:
    * Upload images and generate videos
    * Track generation status
    * Store generation history
    """,
    version="1.0.0",
    docs_url="/docs",   
    redoc_url="/redoc"  
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video.router)

@app.on_event("startup")
async def on_startup():
    await init_db()