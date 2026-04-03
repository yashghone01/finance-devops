from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import time
from dotenv import load_dotenv
load_dotenv()

import re

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/finance_db"
)

# SQLAlchemy 1.4+ requires "postgresql://" instead of "postgres://"
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fix Render's flaky internal DNS by forcing the external Singapore domain
if "dpg-" in DATABASE_URL and ".render.com" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("dpg-d6fc3nh4tr6s73br2k30-a", "dpg-d6fc3nh4tr6s73br2k30-a.singapore-postgres.render.com")

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