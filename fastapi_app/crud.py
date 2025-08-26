from sqlalchemy.orm import Session
from . import models, schemas
from .admin import schemas as admin_schemas
from .admin.security import get_password_hash

# Batch CRUD
def get_batch_by_name(db: Session, name: str):
    return db.query(models.Batch).filter(models.Batch.name == name).first()

def create_batch(db: Session, batch: schemas.BatchCreate):
    db_batch = models.Batch(name=batch.name, telegram_chat_id=batch.telegram_chat_id)
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch

# User CRUD
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate, batch_id: int):
    db_user = models.User(**user.model_dump(), batch_id=batch_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Payment CRUD
def create_payment(db: Session, payment: schemas.PaymentCreate, user_id: int):
    db_payment = models.Payment(**payment.model_dump(), user_id=user_id)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payment_by_payment_id(db: Session, payment_id: str):
    return db.query(models.Payment).filter(models.Payment.razorpay_payment_id == payment_id).first()

def update_payment_invite_link(db: Session, payment_id: str, invite_link: str):
    db_payment = get_payment_by_payment_id(db, payment_id)
    if db_payment:
        db_payment.invite_link = invite_link
        db.commit()
        db.refresh(db_payment)
    return db_payment

def mark_email_as_sent(db: Session, payment_id: str):
    db_payment = get_payment_by_payment_id(db, payment_id)
    if db_payment:
        db_payment.email_sent = True
        db.commit()
        db.refresh(db_payment)
    return db_payment

# Admin CRUD
def get_admin_by_email(db: Session, email: str):
    return db.query(models.Admin).filter(models.Admin.email == email).first()

def create_admin(db: Session, admin: admin_schemas.AdminCreate):
    hashed_password = get_password_hash(admin.password)
    db_admin = models.Admin(email=admin.email, hashed_password=hashed_password)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin 