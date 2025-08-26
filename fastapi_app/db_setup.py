from sqlalchemy import create_engine
from .database import Base
from . import models

DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    Base.metadata.create_all(bind=engine) 