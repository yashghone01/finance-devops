from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from api.database import engine
from api.schemas import ExpenseCreate
from api.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

app = FastAPI()

# -----------------------------
# Startup: Create Tables
# -----------------------------
@app.on_event("startup")
def create_tables():
    query = text("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
            category VARCHAR(100) NOT NULL,
            payment_mode VARCHAR(10) CHECK (payment_mode IN ('CASH','UPI')),
            description TEXT,
            expense_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    with engine.connect() as connection:
        connection.execute(query)
        connection.commit()


# -----------------------------
# CORS Configuration
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Serve Frontend
# -----------------------------
@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")


# =============================
# AUTH ROUTES
# =============================

@app.post("/register")
def register(email: str, password: str):
    hashed = hash_password(password)

    query = text("""
        INSERT INTO users (email, password_hash)
        VALUES (:email, :password_hash)
        RETURNING id
    """)

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {
                "email": email,
                "password_hash": hashed
            })
            conn.commit()
            user_id = result.fetchone()[0]
    except:
        raise HTTPException(status_code=400, detail="Email already exists")

    return {"message": "User created successfully"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    query = text("SELECT id, password_hash FROM users WHERE email = :email")

    with engine.connect() as conn:
        user = conn.execute(query, {"email": form_data.username}).fetchone()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user.id)

    return {"access_token": access_token, "token_type": "bearer"}


# =============================
# EXPENSE ROUTES (PROTECTED)
# =============================

@app.post("/expenses")
def add_expense(
    expense: ExpenseCreate,
    current_user: dict = Depends(get_current_user)
):
    query = text("""
        INSERT INTO transactions
        (amount, category, payment_mode, description, expense_date, user_id)
        VALUES (:amount, :category, :payment_mode, :description, :expense_date, :user_id)
    """)

    data = expense.dict()
    data["user_id"] = current_user["id"]

    with engine.connect() as connection:
        connection.execute(query, data)
        connection.commit()

    return {"message": "Expense added successfully"}


@app.get("/expenses/daily")
def get_daily_total(current_user: dict = Depends(get_current_user)):
    query = text("""
        SELECT SUM(amount)
        FROM transactions
        WHERE expense_date = CURRENT_DATE
        AND user_id = :user_id
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            "user_id": current_user["id"]
        }).scalar()

    return {"daily_total": result or 0}


@app.get("/expenses/monthly")
def get_monthly_total(current_user: dict = Depends(get_current_user)):
    query = text("""
        SELECT SUM(amount)
        FROM transactions
        WHERE date_trunc('month', expense_date) =
              date_trunc('month', CURRENT_DATE)
        AND user_id = :user_id
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            "user_id": current_user["id"]
        }).scalar()

    return {"monthly_total": result or 0}


@app.get("/expenses/history")
def get_recent_expenses(current_user: dict = Depends(get_current_user)):
    query = text("""
        SELECT id, amount, category, payment_mode, description, expense_date
        FROM transactions
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT 10
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            "user_id": current_user["id"]
        })
        rows = [dict(row._mapping) for row in result]

    return rows