from pydantic import BaseModel
from datetime import date

class ExpenseCreate(BaseModel):
    amount: float
    category: str
    payment_mode: str
    description: str
    expense_date: date
    type: str = "EXPENSE"

class BudgetUpdate(BaseModel):
    monthly_budget: float

class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str
    password: str | None = None

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str