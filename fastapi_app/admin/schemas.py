from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Admin Schemas ---
class AdminBase(BaseModel):
    email: EmailStr

class AdminCreate(AdminBase):
    password: str

class Admin(AdminBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# --- Dashboard Schemas ---
class DashboardStats(BaseModel):
    total_users: int
    total_payments: int
    total_batches: int
    total_revenue: float
    payment_status: Dict[str, int]
    users_per_batch: List[Dict[str, Any]]
    recent_payments: List[Dict[str, Any]]
    recent_users: List[Dict[str, Any]]

class PaymentAnalytics(BaseModel):
    daily_payments: List[Dict[str, Any]]
    status_distribution: List[Dict[str, Any]]

class UserAnalytics(BaseModel):
    daily_users: List[Dict[str, Any]]
    batch_distribution: List[Dict[str, Any]]

# --- User Management Schemas ---
class UserList(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    batch_id: int
    batch_name: Optional[str] = None
    payment_count: Optional[int] = 0

    class Config:
        from_attributes = True

class UserDetail(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    batch_id: int
    batch_name: Optional[str] = None
    payments: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    batch_id: Optional[int] = None

# --- Payment Management Schemas ---
class PaymentList(BaseModel):
    id: int
    razorpay_payment_id: str
    razorpay_order_id: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    batch_name: Optional[str] = None

    class Config:
        from_attributes = True

class PaymentDetail(BaseModel):
    id: int
    razorpay_payment_id: str
    razorpay_order_id: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    invite_link: Optional[str] = None
    user: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    invite_link: Optional[str] = None

# --- Batch Management Schemas ---
class BatchList(BaseModel):
    id: int
    name: str
    telegram_chat_id: str
    user_count: Optional[int] = 0

    class Config:
        from_attributes = True

class BatchDetail(BaseModel):
    id: int
    name: str
    telegram_chat_id: str
    users: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

class BatchCreate(BaseModel):
    name: str
    telegram_chat_id: str

class BatchUpdate(BaseModel):
    name: Optional[str] = None
    telegram_chat_id: Optional[str] = None

# --- Search and Filter Schemas ---
class SearchParams(BaseModel):
    query: Optional[str] = None
    status: Optional[str] = None
    batch_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    limit: int = 20

# --- Response Schemas ---
class PaginatedResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    pages: int

class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool
    error: str
    details: Optional[str] = None 