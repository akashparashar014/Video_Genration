import os
import time
import base64
import io
import shutil
import requests
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from PIL import Image
from runwayml import RunwayML
from app.database import get_db
from app.model import GeneratedVideo
from pydantic import BaseModel
from typing import Optional

router = APIRouter(
    prefix="/api/v1",
    tags=["Video Generation"]
)

os.environ['RUNWAYML_API_SECRET'] = 'key_a1ee9d74b4100b243212cc2f8ade81aaa4b8691fe736a3bbd193cd0b3d28b49d255e4a51e083efb417d8dd2993794d87a4a7a8037688f0d250e8b75b3e5a4692'
client = RunwayML()

UPLOAD_DIR = Path("uploads") 
UPLOAD_DIR.mkdir(exist_ok=True)

class VideoResponse(BaseModel):
    task_id: str
    prompt: str
    video_url: str

@router.post("/generate-video/", response_model=VideoResponse, summary="Generate Video from Image")

async def generate_video(
    image: UploadFile = File(
        ...,
        description="Image file to generate video from (JPEG or PNG)"
    ),
    prompt: str = Form(
        ...,
        description="Text prompt describing the desired video",
    ),
    db: AsyncSession = Depends(get_db)
):
    if not image.content_type in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG and PNG images are supported"
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
            print(len(base64_encoded))

        if len(base64_encoded) > 2048:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image too large after encoding. Please resize further."
            )

        task = client.image_to_video.create(
            model='gen3a_turbo',
            prompt_image=base64_encoded,
            prompt_text=prompt
        )

        task_id = task.id
        print(f"Task ID: {task_id}")

        attempts = 0
        max_attempts = 60  

        while attempts < max_attempts:
            task_info = client.tasks.retrieve(id=task_id)
            print(f"Task Status: {task_info.status}")

            if task_info.status == "SUCCEEDED":
                break
            elif task_info.status == "FAILED":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Task failed: {task_info.failure}"
                )
            
            time.sleep(5)
            attempts += 1

        if attempts >= max_attempts:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Video generation timed out"
            )

        video_url = task_info.output[0]
        print(f"Generated Video URL: {video_url}")

        new_entry = GeneratedVideo(
            task_id=task_id,
            prompt=prompt,
            original_image=str(original_image_path),
            base64_image=base64_encoded,
            video_url=video_url
        )
        db.add(new_entry)
        await db.commit()
        await db.refresh(new_entry)

        return VideoResponse(task_id=task_id, prompt=prompt, video_url=video_url)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get(
    "/status/{task_id}",
    response_model=VideoResponse,
    summary="Get Video Generation Status",
    description="Retrieve the status and video URL for a specific task ID"
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


# import os
# import time
# import base64
# import io
# import shutil
# import requests
# from pathlib import Path
# from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from PIL import Image
# from runwayml import RunwayML
# from app.database import get_db
# from app.model import GeneratedVideo

# router = APIRouter()

# os.environ['RUNWAYML_API_SECRET'] = 'key_a1ee9d74b4100b243212cc2f8ade81aaa4b8691fe736a3bbd193cd0b3d28b49d255e4a51e083efb417d8dd2993794d87a4a7a8037688f0d250e8b75b3e5a4692'
# client = RunwayML()

# UPLOAD_DIR = Path("uploads") 
# UPLOAD_DIR.mkdir(exist_ok=True)

# @router.post("/generate-video/")
# async def generate_video(
#     image: UploadFile = File(...),
#     prompt: str = Form(...),
#     db: AsyncSession = Depends(get_db)
# ):
#     original_image_path = UPLOAD_DIR / image.filename
#     with original_image_path.open("wb") as buffer:
#         shutil.copyfileobj(image.file, buffer)

#     with Image.open(original_image_path) as img:
#         if img.mode == 'RGBA':
#             img = img.convert('RGB')
        
#         img.thumbnail((100, 100), Image.Resampling.LANCZOS)
        
#         buffer = io.BytesIO()
#         img.save(buffer, format="JPEG", quality=20)
#         buffer.seek(0)

#         base64_encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
#         base64_encoded = f"data:image/jpeg;base64,{base64_encoded}"

#     if len(base64_encoded) > 2048:
#         return HTTPException(status_code=400, detail="Image too large after encoding. Please resize further.")

#     task = client.image_to_video.create(
#         model='gen3a_turbo',
#         prompt_image=base64_encoded,
#         prompt_text=prompt
#     )

#     task_id = task.id
#     print(f"Task Created! Task ID: {task_id}")

#     while True:
#         task_info = client.tasks.retrieve(id=task_id)
#         print(f"Task Status: {task_info.status}")

#         if task_info.status == "SUCCEEDED":
#             break
#         elif task_info.status == "FAILED":
#             return HTTPException(status_code=500, detail=f"Task failed: {task_info.failure}")
        
#         time.sleep(5)  

#     video_url = task_info.output[0]
#     print(f"Generated Video URL: {video_url}")

#     new_entry = GeneratedVideo(
#         task_id=task_id,
#         prompt=prompt,
#         original_image=str(original_image_path),
#         base64_image=base64_encoded,
#         video_url=video_url
#     )
#     db.add(new_entry)
#     await db.commit()
#     await db.refresh(new_entry)

#     return {"task_id": task_id, "video_url": video_url}
