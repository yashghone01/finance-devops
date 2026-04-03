from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import time
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/finance_db"
)

# Standard engine creation (SQAlchemy handles connection pooling)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Automatically check if connection is alive
    connect_args={"connect_timeout": 10} # Don't hang for more than 10s
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)