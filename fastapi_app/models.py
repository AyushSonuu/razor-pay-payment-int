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

    batch = relationship("Batch", back_populates="users")
    payments = relationship("Payment", back_populates="user")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    razorpay_payment_id = Column(String, unique=True, index=True)
    razorpay_order_id = Column(String, index=True)
    amount = Column(Float)
    currency = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    invite_link = Column(String, nullable=True)
    email_sent = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="payments") 