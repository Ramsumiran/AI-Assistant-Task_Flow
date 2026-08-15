import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load .env file
load_dotenv()

# Read DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found. Check your .env file.")

#print("DATABASE_URL =", DATABASE_URL)

# Create engine

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Session
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# Base class
class Base(DeclarativeBase):
    pass


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()