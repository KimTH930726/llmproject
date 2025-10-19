from sqlmodel import create_engine, SQLModel, Session
import os
from dotenv import load_dotenv

load_dotenv()

# 데이터베이스 URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# 엔진 생성
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    """데이터베이스 및 테이블 생성"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """세션 생성 (의존성 주입용)"""
    with Session(engine) as session:
        yield session
