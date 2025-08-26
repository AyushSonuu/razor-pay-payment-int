import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    telegram_chat_id = Column(String)
    users = relationship("User", back_populates="batch")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, index=True)
    phone = Column(String, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"))
    invite_link = Column(String, nullable=True)

    batch = relationship("Batch", back_populates="users")
    payments = relationship("Payment", back_populates="user")

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    razorpay_payment_id = Column(String, unique=True, index=True)
    razorpay_order_id = Column(String, index=True)
    amount = Column(Float)
    currency = Column(String)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    user = relationship("User", back_populates="payments")

class ProcessingLock(Base):
    __tablename__ = "processing_locks"

    payment_id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc)) 