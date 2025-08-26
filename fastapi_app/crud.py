from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, case
from datetime import datetime, timedelta, timezone
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

def get_all_batches(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Batch).offset(skip).limit(limit).all()

def get_batch_by_id(db: Session, batch_id: int):
    return db.query(models.Batch).filter(models.Batch.id == batch_id).first()

def update_batch(db: Session, batch_id: int, batch_data: dict):
    db_batch = get_batch_by_id(db, batch_id)
    if db_batch:
        for key, value in batch_data.items():
            setattr(db_batch, key, value)
        db.commit()
        db.refresh(db_batch)
    return db_batch

def delete_batch(db: Session, batch_id: int):
    db_batch = get_batch_by_id(db, batch_id)
    if db_batch:
        db.delete(db_batch)
        db.commit()
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

def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def update_user(db: Session, user_id: int, user_data: dict):
    db_user = get_user_by_id(db, user_id)
    if db_user:
        for key, value in user_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def get_users_by_batch(db: Session, batch_id: int):
    return db.query(models.User).filter(models.User.batch_id == batch_id).all()

# Payment CRUD
def create_payment(db: Session, payment: schemas.PaymentCreate, user_id: int):
    print(f"CRUD: Attempting to create payment for payment_id={payment.razorpay_payment_id}")
    db_payment = models.Payment(**payment.model_dump(), user_id=user_id)
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

def get_payment_by_payment_id(db: Session, payment_id: str):
    return db.query(models.Payment).filter(models.Payment.razorpay_payment_id == payment_id).first()

def update_payment_status(db: Session, payment_id: str, status: str, email_sent: bool = None):
    log_msg = f"CRUD: Attempting to update payment_id={payment_id} to status='{status}'"
    if email_sent is not None:
        log_msg += f" and email_sent={email_sent}"
    print(log_msg)
    
    db_payment = get_payment_by_payment_id(db, payment_id)
    if db_payment:
        db_payment.status = status
        if email_sent is not None:
            db_payment.email_sent = email_sent
        db.commit()
        db.refresh(db_payment)
    return db_payment

def get_all_payments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Payment).offset(skip).limit(limit).all()

def get_payment_by_id(db: Session, payment_id: int):
    return db.query(models.Payment).filter(models.Payment.id == payment_id).first()

def get_payments_by_status(db: Session, status: str):
    return db.query(models.Payment).filter(models.Payment.status == status).all()

def get_payments_by_date_range(db: Session, start_date: datetime, end_date: datetime):
    return db.query(models.Payment).filter(
        and_(
            models.Payment.created_at >= start_date,
            models.Payment.created_at <= end_date
        )
    ).all()

def update_payment_invite_link(db: Session, payment_id: str, invite_link: str):
    db_payment = get_payment_by_payment_id(db, payment_id)
    if db_payment and db_payment.user:
        db_payment.user.invite_link = invite_link
        db.commit()
        db.refresh(db_payment.user)
    return db_payment.user if db_payment else None

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

def get_all_admins(db: Session):
    return db.query(models.Admin).all()

def get_admin_by_id(db: Session, admin_id: int):
    return db.query(models.Admin).filter(models.Admin.id == admin_id).first()

# Analytics CRUD
def get_dashboard_stats(db: Session):
    """Get comprehensive dashboard statistics"""
    total_users = db.query(func.count(models.User.id)).scalar()
    total_payments = db.query(func.count(models.Payment.id)).scalar()
    total_batches = db.query(func.count(models.Batch.id)).scalar()
    
    # Payment status counts
    completed_payments = db.query(func.count(models.Payment.id)).filter(models.Payment.status == "completed").scalar()
    pending_payments = db.query(func.count(models.Payment.id)).filter(models.Payment.status == "pending").scalar()
    failed_payments = db.query(func.count(models.Payment.id)).filter(models.Payment.status == "failed").scalar()
    processing_payments = db.query(func.count(models.Payment.id)).filter(models.Payment.status == "processing").scalar()
    
    # Total revenue
    total_revenue = db.query(func.sum(models.Payment.amount)).filter(models.Payment.status == "completed").scalar() or 0
    
    # Users per batch
    users_per_batch_query = db.query(
        models.Batch.name,
        func.count(models.User.id).label('user_count')
    ).join(models.User).group_by(models.Batch.id, models.Batch.name).all()
    users_per_batch = [{"name": b.name, "user_count": b.user_count} for b in users_per_batch_query]
    
    # Recent payments (last 10)
    recent_payments_query = db.query(models.Payment).order_by(desc(models.Payment.created_at)).limit(10).all()
    recent_payments = [{
        "amount": p.amount,
        "razorpay_payment_id": p.razorpay_payment_id,
        "status": p.status,
        "user": {"name": p.user.name if p.user else "Unknown"}
    } for p in recent_payments_query]
    
    # Recent users (last 10)
    recent_users_query = db.query(models.User).order_by(desc(models.User.id)).limit(10).all()
    recent_users = [{
        "name": u.name,
        "email": u.email,
        "batch": {"name": u.batch.name if u.batch else "No batch"}
    } for u in recent_users_query]
    
    return {
        "total_users": total_users,
        "total_payments": total_payments,
        "total_batches": total_batches,
        "total_revenue": total_revenue,
        "payment_status": {
            "completed": completed_payments,
            "pending": pending_payments,
            "failed": failed_payments,
            "processing": processing_payments
        },
        "users_per_batch": users_per_batch,
        "recent_payments": recent_payments,
        "recent_users": recent_users
    }

def get_payment_analytics(db: Session, days: int = 30):
    """Get payment analytics for the last N days"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Daily payment counts and revenue for completed payments
    daily_payments_query = db.query(
        func.date(models.Payment.created_at).label('date'),
        func.count(models.Payment.id).label('count'),
        func.sum(
            case(
                (models.Payment.status == "completed", models.Payment.amount),
                else_=0
            )
        ).label('revenue')
    ).filter(
        models.Payment.created_at.between(start_date, end_date)
    ).group_by(func.date(models.Payment.created_at)).all()
    
    # Payment status distribution for the period
    status_distribution_query = db.query(
        models.Payment.status,
        func.count(models.Payment.id).label('count')
    ).filter(
        models.Payment.created_at.between(start_date, end_date)
    ).group_by(models.Payment.status).all()
    status_distribution = [{"status": s.status, "count": s.count} for s in status_distribution_query]
    
    # Create a dictionary for quick lookup
    payments_by_date = {str(p.date): {"count": p.count, "revenue": p.revenue or 0} for p in daily_payments_query}
    
    # Generate a full date range to ensure no gaps in the chart
    result_daily_payments = []
    for i in range(days + 1):
        current_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        data = payments_by_date.get(current_date, {"count": 0, "revenue": 0})
        result_daily_payments.append({
            "date": current_date,
            "count": data["count"],
            "revenue": data["revenue"]
        })

    return {
        "daily_payments": result_daily_payments,
        "status_distribution": status_distribution
    }

def get_user_analytics(db: Session, days: int = 30):
    """Get user analytics for the last N days"""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Users joined per day
    daily_users_query = db.query(
        func.date(models.User.created_at).label('date'),
        func.count(models.User.id).label('count')
    ).filter(
        models.User.created_at.between(start_date, end_date)
    ).group_by(func.date(models.User.created_at)).order_by(func.date(models.User.created_at)).all()
    
    # Users per batch for new users in the period
    batch_distribution_query = db.query(
        models.Batch.name,
        func.count(models.User.id).label('count')
    ).join(models.User).filter(
        models.User.created_at.between(start_date, end_date)
    ).group_by(models.Batch.id, models.Batch.name).all()
    batch_distribution = [{"name": b.name, "count": b.count} for b in batch_distribution_query]
    
    # Create a dictionary for quick lookup
    users_by_date = {str(u.date): u.count for u in daily_users_query}

    # Generate a full date range to ensure no gaps in the chart
    result_daily_users = []
    for i in range(days + 1):
        current_date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        count = users_by_date.get(current_date, 0)
        result_daily_users.append({"date": current_date, "count": count})

    return {
        "daily_users": result_daily_users,
        "batch_distribution": batch_distribution
    }

# Settings CRUD
def get_setting(db: Session, key: str):
    return db.query(models.Setting).filter(models.Setting.key == key).first()

def get_all_settings(db: Session):
    return db.query(models.Setting).all()

def update_setting(db: Session, key: str, value: str):
    db_setting = get_setting(db, key)
    if db_setting:
        db_setting.value = value
    else:
        db_setting = models.Setting(key=key, value=value)
        db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

def get_settings_as_dict(db: Session):
    settings = get_all_settings(db)
    return {setting.key: setting.value for setting in settings}

# Processing Lock CRUD
def remove_processing_lock(db: Session, payment_id: str):
    """Finds and removes a processing lock from the database."""
    lock_to_delete = db.query(models.ProcessingLock).filter(models.ProcessingLock.payment_id == payment_id).first()
    if lock_to_delete:
        db.delete(lock_to_delete)
        db.commit() 