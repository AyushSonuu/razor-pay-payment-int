from pydantic import BaseModel, EmailStr

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