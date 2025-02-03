from sqlalchemy import Column, Integer, String, LargeBinary
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False) 
    email = Column(String(100), unique=True, index=True, nullable=False)   
    password_hash = Column(String(255), nullable=False)                    
    
    class Config:
        orm_mode = True  
        
        
class GeneratedVideo(Base):
    __tablename__ = "generated_videos"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    prompt = Column(String, nullable=False)
    original_image = Column(LargeBinary(255), nullable=False)  
    base64_image = Column(String, nullable=False) 
    video_url = Column(String, nullable=False) 

    class Config:
        orm_mode = True   
        
        
class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, nullable=False) 
    size_kb = Column(Integer, nullable=False) 
    audio_data = Column(LargeBinary, nullable=False)  
    
    class Config:
        orm_mode = True