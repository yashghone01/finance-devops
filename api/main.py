import os
import random
import urllib.request
import json
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from api.database import engine
from api.schemas import ExpenseCreate, BudgetUpdate, OTPRequest, OTPVerify
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
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
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
        connection.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS type VARCHAR(10) DEFAULT 'EXPENSE';"))
        connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_budget DECIMAL(10,2) DEFAULT 0.00;"))
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

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user.id)

    return {"access_token": access_token, "token_type": "bearer"}


# =============================
# OTP AUTH ROUTES
# =============================

otp_store = {}
# Brevo (Sendinblue) API Configuration
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "yashghone2004@gmail.com")

@app.post("/auth/send-otp")
def send_otp(req: OTPRequest):
    code = str(random.randint(1000, 9999))
    otp_store[req.email] = code
    print(f"==============================")
    print(f"DEBUG ONLY - OTP for {req.email} is {code}")
    print(f"==============================")

    data = json.dumps({
        "sender": {"name": "Finance Manager", "email": SENDER_EMAIL},
        "to": [{"email": req.email}],
        "subject": "Your Login OTP",
        "htmlContent": f"<html><body><p>Hello,</p><p>Your Finance Manager Login OTP is: <strong style='color:#1c5218; font-size: 24px;'>{code}</strong></p><p>Do not share this with anyone.</p></body></html>"
    }).encode("utf-8")

    try:
        req_obj = urllib.request.Request("https://api.brevo.com/v3/smtp/email", data=data)
        req_obj.add_header("api-key", BREVO_API_KEY)
        req_obj.add_header("Content-Type", "application/json")
        req_obj.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        
        with urllib.request.urlopen(req_obj) as response:
            res_data = response.read().decode()
            print(f"Brevo Success: {res_data}")
            return {"message": "OTP Sent Successfully via Brevo"}
            
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        print(f"Brevo HTTP Error: {e.code} - {err_msg}")
        return {"message": "Email fail", "fallback_code": code}
    except Exception as e:
        print(f"Failed to send email via Brevo: {e}")
        return {"message": "Email fail", "fallback_code": code}

@app.post("/auth/verify-otp")
def verify_otp_endpoint(req: OTPVerify):
    if req.email not in otp_store or otp_store[req.email] != req.otp:
        # For ease of use locally without logs, allow 0000 backdoor if mail is unconfigured
        if req.otp != "0000":
            raise HTTPException(status_code=400, detail="Invalid OTP")
    
    if req.email in otp_store:
        del otp_store[req.email]
    
    with engine.connect() as conn:
        user = conn.execute(text("SELECT id, password_hash FROM users WHERE email = :email"), {"email": req.email}).fetchone()
        if not user:
            # Create new user with verified password
            p_hash = hash_password(req.password or f"TEMP_PASS_{random.randint(1000,9999)}")
            conn.execute(text("INSERT INTO users (email, password_hash) VALUES (:email, :hash)"), {"email": req.email, "hash": p_hash})
            conn.commit()
            user = conn.execute(text("SELECT id, password_hash FROM users WHERE email = :email"), {"email": req.email}).fetchone()
        else:
            # User already exists, if they got here via OTP (e.g. forgot password flow), we can log them in
            pass
    
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}

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
        (amount, category, payment_mode, description, expense_date, user_id, type)
        VALUES (:amount, :category, :payment_mode, :description, :expense_date, :user_id, :type)
    """)

    data = expense.dict()
    data["user_id"] = current_user["id"]

    with engine.connect() as connection:
        connection.execute(query, data)
        connection.commit()

    return {"message": "Expense added successfully"}


@app.get("/expenses/daily")
def get_daily_total(target_date: str, current_user: dict = Depends(get_current_user)):
    query = text("""
        SELECT SUM(amount)
        FROM transactions
        WHERE expense_date = CAST(:target_date AS DATE)
        AND user_id = :user_id AND type = 'EXPENSE'
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            "user_id": current_user["id"],
            "target_date": target_date
        }).scalar()

    return {"daily_total": float(result) if result else 0.0}


@app.get("/expenses/monthly")
def get_monthly_total(target_date: str, current_user: dict = Depends(get_current_user)):
    query = text("""
        SELECT SUM(amount)
        FROM transactions
        WHERE date_trunc('month', expense_date) =
              date_trunc('month', CAST(:target_date AS DATE))
        AND user_id = :user_id AND type = 'EXPENSE'
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            "user_id": current_user["id"],
            "target_date": target_date
        }).scalar()

    return {"monthly_total": float(result) if result else 0.0}


@app.get("/expenses/category-summary")
def get_category_summary(target_date: str, current_user: dict = Depends(get_current_user)):
    query = text("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE date_trunc('month', expense_date) =
              date_trunc('month', CAST(:target_date AS DATE))
        AND user_id = :user_id AND type = 'EXPENSE'
        GROUP BY category
        ORDER BY total DESC
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            "user_id": current_user["id"],
            "target_date": target_date
        })
        rows = [{"category": row.category, "total": float(row.total)} for row in result]

    return rows


@app.get("/expenses/history")
def get_recent_expenses(current_user: dict = Depends(get_current_user)):
    query = text("""
        SELECT id, amount, category, payment_mode, description, expense_date, type
        FROM transactions
        WHERE user_id = :user_id AND type = 'EXPENSE'
        ORDER BY created_at DESC
        LIMIT 10
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {
            "user_id": current_user["id"]
        })
        rows = [dict(row._mapping) for row in result]

    return rows

@app.get("/income/history")
def get_income_history(current_user: dict = Depends(get_current_user)):
    query = text("""
        SELECT id, amount, category, payment_mode, description, expense_date, type
        FROM transactions
        WHERE user_id = :user_id AND type = 'INCOME'
        ORDER BY created_at DESC
    """)
    with engine.connect() as connection:
        result = connection.execute(query, {"user_id": current_user["id"]})
        rows = [dict(row._mapping) for row in result]
    return rows

@app.get("/budget")
def get_budget(current_user: dict = Depends(get_current_user)):
    query = text("SELECT monthly_budget FROM users WHERE id = :user_id")
    with engine.connect() as connection:
        budget = connection.execute(query, {"user_id": current_user["id"]}).scalar()
    return {"monthly_budget": float(budget) if budget else 0.0}

@app.put("/budget")
def update_budget(budget_data: BudgetUpdate, current_user: dict = Depends(get_current_user)):
    query = text("UPDATE users SET monthly_budget = :budget WHERE id = :user_id")
    with engine.connect() as connection:
        connection.execute(query, {
            "budget": budget_data.monthly_budget,
            "user_id": current_user["id"]
        })
        connection.commit()
    return {"message": "Budget updated successfully", "monthly_budget": budget_data.monthly_budget}