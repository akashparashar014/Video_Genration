import os
import uuid
import base64
import io
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from PIL import Image
from app.database import get_db
from app.model import GeneratedVideo
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/v2",
    tags=["Video Generation 01"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class VideoResponse(BaseModel):
    task_id: str
    prompt: str
    video_url: str

@router.post(
    "/generate-video-1/",
    response_model=VideoResponse,
    summary="Generate Video from Image (Dummy Response)"
)
async def generate_video(
    image: UploadFile = File(..., description="Image file (JPEG or PNG)"),
    prompt: str = Form(..., description="Text prompt for video"),
    db: AsyncSession = Depends(get_db)
):
    if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, JPG and PNG images are supported"
        )

    try:
        original_image_path = UPLOAD_DIR / image.filename
        with original_image_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        with Image.open(original_image_path) as img:
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            img.thumbnail((100, 100), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=20)
            buffer.seek(0)

            base64_encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
            base64_encoded = f"data:image/jpeg;base64,{base64_encoded}"

        if len(base64_encoded) > 2048:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image too large after encoding. Please resize further."
            )

        task_id = str(uuid.uuid4())
        dummy_video_url = "https://www.example.com/dummy_video.mp4"

        print(f"Generated Dummy Video: {dummy_video_url}")

        image_bytes = await image.read()        
            
        new_entry = GeneratedVideo(
            task_id=task_id,
            prompt=prompt,
            original_image=image_bytes,
            base64_image=base64_encoded,
            video_url=dummy_video_url
        )
        
        db.add(new_entry)
        await db.commit()
        await db.refresh(new_entry)

        return VideoResponse(task_id=task_id,
            prompt=prompt,
            video_url=dummy_video_url
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/status-1/{task_id}",
    response_model=VideoResponse,
    summary="Get Video Status (Dummy Response)"
)
async def get_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(GeneratedVideo).where(GeneratedVideo.task_id == task_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return VideoResponse(task_id=video.task_id, video_url=video.video_url)
