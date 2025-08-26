from pydantic import BaseModel
from typing import Optional
import datetime

class PaymentBase(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    amount: float
    currency: str
    status: str
    invite_link: Optional[str] = None
    email_sent: bool = False

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: int
    user_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    name: str
    email: str
    phone: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    batch_id: int
    payments: list[Payment] = []

    class Config:
        from_attributes = True

class BatchBase(BaseModel):
    name: str
    telegram_chat_id: str

class BatchCreate(BatchBase):
    pass

class Batch(BatchBase):
    id: int
    users: list[User] = []

    class Config:
        from_attributes = True

class OrderRequest(BaseModel):
    batchType: str
    name: str
    email: str
    phone: str
    amount: int 