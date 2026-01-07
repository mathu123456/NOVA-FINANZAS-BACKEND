from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# ============= USER SCHEMAS =============
class UserBase(BaseModel):
    username: str
    email: EmailStr
    currency: str = "USD"
    daily_limit: float = 0.0

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# ============= CATEGORY SCHEMAS =============
class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= EXPENSE SCHEMAS =============
class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str
    category_id: int
    note: Optional[str] = None
    date: Optional[datetime] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    category_id: Optional[int] = None
    note: Optional[str] = None
    date: Optional[datetime] = None

class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= BUDGET SCHEMAS =============
class BudgetBase(BaseModel):
    amount: float = Field(..., gt=0)
    category_id: Optional[int] = None  # None = presupuesto global
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000)

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)

class BudgetResponse(BudgetBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= USER SETTINGS SCHEMAS =============
class UserSettingsBase(BaseModel):
    theme: str = "light"
    alerts_enabled: bool = True
    alert_frequency_minutes: int = Field(default=150, ge=30)
    alert_start_hour: int = Field(default=8, ge=0, le=23)
    alert_end_hour: int = Field(default=22, ge=0, le=23)

class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = None
    alerts_enabled: Optional[bool] = None
    alert_frequency_minutes: Optional[int] = Field(None, ge=30)
    alert_start_hour: Optional[int] = Field(None, ge=0, le=23)
    alert_end_hour: Optional[int] = Field(None, ge=0, le=23)

class UserSettingsResponse(UserSettingsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============= REPORT SCHEMAS =============
class DailySummary(BaseModel):
    date: str
    total: float
    currency: str
    expenses_count: int

class CategorySummary(BaseModel):
    category_name: str
    total: float
    percentage: float

class BudgetStatus(BaseModel):
    budget_amount: float
    spent: float
    remaining: float
    percentage_used: float
    is_exceeded: bool
    category_name: Optional[str] = None

class ComparativeReport(BaseModel):
    current_month_total: float
    previous_month_total: float
    difference_absolute: float
    difference_percentage: float
    average_last_3_months: float
    difference_vs_average: float