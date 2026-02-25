from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import time

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@db:5432/finance_db"
)

# Retry connection until DB is ready
for i in range(10):
    try:
        engine = create_engine(DATABASE_URL)
        connection = engine.connect()
        connection.close()
        print("Database connected successfully.")
        break
    except Exception as e:
        print("Database not ready, retrying...")
        time.sleep(3)
else:
    raise Exception("Could not connect to database.")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)