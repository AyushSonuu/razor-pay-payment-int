import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .database import Base, SessionLocal
from . import models, crud
from .admin import schemas as admin_schemas

DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(DATABASE_URL)

def create_initial_admin(db: sessionmaker):
    initial_email = os.getenv("ADMIN_EMAIL", "support@genanimate.com")
    initial_pass = os.getenv("ADMIN_PASS", "Sarjsssk@mbl5508")
    
    admin = crud.get_admin_by_email(db, email=initial_email)
    if not admin:
        admin_in = admin_schemas.AdminCreate(email=initial_email, password=initial_pass)
        crud.create_admin(db, admin=admin_in)
        print(f"Initial admin user '{initial_email}' created.")

def create_initial_settings(db: sessionmaker):
    # These are the settings that can be managed via the admin panel
    managed_settings = [
        "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET",
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID_MORNING", "TELEGRAM_CHAT_ID_EVENING",
        "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"
    ]
    
    for key in managed_settings:
        setting = crud.get_setting(db, key=key)
        if not setting:
            value = os.getenv(key)
            if value is not None:
                crud.update_setting(db, key=key, value=value)
    print("Initial settings populated from .env file.")

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)
    # Create the initial admin user after tables are created
    db = SessionLocal()
    try:
        create_initial_admin(db)
        create_initial_settings(db)
    finally:
        db.close() 