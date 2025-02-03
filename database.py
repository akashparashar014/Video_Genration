from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from typing import Generator

DATABASE_URL = "postgresql+asyncpg://postgres:auriga123@localhost:5432/social_media"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,  
    pool_size=5,         
    max_overflow=10
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def init_db() -> None:
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError as e:
        print(f"Error initializing database: {e}")
        raise

async def get_db() -> Generator[AsyncSession, None, None]:
    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        await session.rollback()
        raise
    finally:
        await session.close()