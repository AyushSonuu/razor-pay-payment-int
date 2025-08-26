from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud
from . import schemas
from .security import verify_password
# Add JWT/session management imports here later

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

templates = Jinja2Templates(directory="fastapi_app/admin/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db), email: str = Form(...), password: str = Form(...)):
    admin = crud.get_admin_by_email(db, email=email)
    if not admin or not verify_password(password, admin.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password"
        })
    
    # In a real app, you'd create a session token here.
    # For now, we'll redirect to a placeholder dashboard.
    response = RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
    # Set session cookie here, e.g., response.set_cookie(key="session_token", value=token)
    return response

# Placeholder for the dashboard
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # This will be protected by an auth dependency later
    return templates.TemplateResponse("dashboard.html", {"request": request}) 