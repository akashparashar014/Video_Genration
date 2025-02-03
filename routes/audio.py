from fastapi import UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.model import AudioFile
from fastapi.responses import StreamingResponse
from sqlalchemy.future import select
from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class AudioFileResponse(BaseModel):
    id: int
    filename: str
    size_kb: int

    class Config:
        orm_mode = True


@router.post("/upload/")
async def upload_audio(
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db)
):

    if not file.filename.endswith(".mp3"):
        raise HTTPException(status_code=400, detail="Only MP3 files are allowed.")

    audio_binary = await file.read()
    file_size_kb = round(len(audio_binary) / 1024, 2)  

    new_audio = AudioFile(
        filename=file.filename,
        size_kb=file_size_kb,
        audio_data=audio_binary
    )

    db.add(new_audio)
    await db.commit()
    await db.refresh(new_audio)

    return {"message": "File uploaded", "filename": file.filename, "size_kb": file_size_kb}


@router.get("/play/{filename}")
async def play_audio(filename: str, db: AsyncSession = Depends(get_db)):
    
    result = await db.execute(select(AudioFile).where(AudioFile.filename == filename))
    audio_file = result.scalar_one_or_none()
    
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found.")

    return StreamingResponse(
        iter([audio_file.audio_data]), 
        media_type="audio/mpeg"
    )
    

@router.get("/list/", response_model=list[AudioFileResponse])
async def list_audio_files(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AudioFile))
    audio_files = result.scalars().all()
    return audio_files