from pydantic import BaseModel
from datetime import date

class ExpenseCreate(BaseModel):
    amount: float
    category: str
    payment_mode: str
    description: str
    expense_date: date