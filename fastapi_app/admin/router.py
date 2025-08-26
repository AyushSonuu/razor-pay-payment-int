from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import os

from ..database import get_db
from .. import crud, models
from . import schemas
from .security import verify_password

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)

templates = Jinja2Templates(directory="fastapi_app/admin/templates")

# --- Authentication Routes ---
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

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_token")
    return response

# --- Dashboard Routes ---
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/api/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get comprehensive dashboard statistics"""
    try:
        stats = crud.get_dashboard_stats(db)
        return JSONResponse({
            "success": True,
            "data": stats
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/dashboard/analytics/payments")
async def get_payment_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get payment analytics for the specified number of days"""
    try:
        analytics = crud.get_payment_analytics(db, days=days)
        return JSONResponse({
            "success": True,
            "data": analytics
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/dashboard/analytics/users")
async def get_user_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get user analytics for the specified number of days"""
    try:
        analytics = crud.get_user_analytics(db, days=days)
        return JSONResponse({
            "success": True,
            "data": analytics
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Analytics Routes ---
@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})

# --- User Management Routes ---
@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})

@router.get("/api/users")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    batch_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Get paginated list of users with optional filtering"""
    try:
        skip = (page - 1) * limit
        
        # Build query with filters
        query = db.query(models.User)
        
        if search:
            query = query.filter(
                models.User.name.contains(search) |
                models.User.email.contains(search) |
                models.User.phone.contains(search)
            )
        
        if batch_id:
            query = query.filter(models.User.batch_id == batch_id)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        users = query.offset(skip).limit(limit).all()
        
        # Convert to dict with additional info
        user_list = []
        for user in users:
            user_dict = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "batch_id": user.batch_id,
                "batch_name": user.batch.name if user.batch else None,
                "payment_count": len(user.payments)
            }
            user_list.append(user_dict)
        
        return JSONResponse({
            "success": True,
            "data": {
                "users": user_list,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/users/{user_id}")
async def get_user_detail(user_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific user"""
    try:
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "batch_id": user.batch_id,
            "batch_name": user.batch.name if user.batch else None,
            "payments": [
                {
                    "id": payment.id,
                    "razorpay_payment_id": payment.razorpay_payment_id,
                    "amount": payment.amount,
                    "status": payment.status,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None
                }
                for payment in user.payments
            ]
        }
        
        return JSONResponse({
            "success": True,
            "data": user_data
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/users/{user_id}")
async def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db)
):
    """Update user information"""
    try:
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        update_data = user_update.model_dump(exclude_unset=True)
        updated_user = crud.update_user(db, user_id, update_data)
        
        return JSONResponse({
            "success": True,
            "message": "User updated successfully",
            "data": {
                "id": updated_user.id,
                "name": updated_user.name,
                "email": updated_user.email,
                "phone": updated_user.phone,
                "batch_id": updated_user.batch_id
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user"""
    try:
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        crud.delete_user(db, user_id)
        
        return JSONResponse({
            "success": True,
            "message": "User deleted successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Payment Management Routes ---
@router.get("/payments", response_class=HTMLResponse)
async def payments_page(request: Request):
    return templates.TemplateResponse("payments.html", {"request": request})

@router.get("/api/payments")
async def get_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get paginated list of payments with optional filtering"""
    try:
        skip = (page - 1) * limit
        
        # Build query with filters
        query = db.query(models.Payment)
        
        if status:
            query = query.filter(models.Payment.status == status)
        
        if search:
            query = query.join(models.User).filter(
                models.User.name.contains(search) |
                models.User.email.contains(search) |
                models.Payment.razorpay_payment_id.contains(search)
            )
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(models.Payment.created_at >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(models.Payment.created_at <= end_dt)
        
        # Get total count
        total = query.count()
        
        # Get paginated results
        payments = query.order_by(models.Payment.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convert to dict with additional info
        payment_list = []
        for payment in payments:
            payment_dict = {
                "id": payment.id,
                "razorpay_payment_id": payment.razorpay_payment_id,
                "razorpay_order_id": payment.razorpay_order_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "user_name": payment.user.name if payment.user else None,
                "user_email": payment.user.email if payment.user else None,
                "batch_name": payment.user.batch.name if payment.user and payment.user.batch else None
            }
            payment_list.append(payment_dict)
        
        return JSONResponse({
            "success": True,
            "data": {
                "payments": payment_list,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/payments/{payment_id}")
async def get_payment_detail(payment_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific payment"""
    try:
        payment = crud.get_payment_by_id(db, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        payment_data = {
            "id": payment.id,
            "razorpay_payment_id": payment.razorpay_payment_id,
            "razorpay_order_id": payment.razorpay_order_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "invite_link": payment.invite_link,
            "user": {
                "id": payment.user.id,
                "name": payment.user.name,
                "email": payment.user.email,
                "phone": payment.user.phone,
                "batch_name": payment.user.batch.name if payment.user.batch else None
            } if payment.user else None
        }
        
        return JSONResponse({
            "success": True,
            "data": payment_data
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/payments/{payment_id}")
async def update_payment(
    payment_id: int,
    payment_update: schemas.PaymentUpdate,
    db: Session = Depends(get_db)
):
    """Update payment information"""
    try:
        payment = crud.get_payment_by_id(db, payment_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        update_data = payment_update.model_dump(exclude_unset=True)
        
        if "status" in update_data:
            crud.update_payment_status(db, payment.razorpay_payment_id, update_data["status"])
        
        if "invite_link" in update_data:
            if payment.user:
                crud.update_user(db, user_id=payment.user.id, user_data={"invite_link": update_data["invite_link"]})

        return JSONResponse({
            "success": True,
            "message": "Payment updated successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Batch Management Routes ---
@router.get("/batches", response_class=HTMLResponse)
async def batches_page(request: Request):
    return templates.TemplateResponse("batches.html", {"request": request})

@router.get("/api/batches")
async def get_batches(db: Session = Depends(get_db)):
    """Get all batches with user counts"""
    try:
        batches = crud.get_all_batches(db)
        
        batch_list = []
        for batch in batches:
            user_count = len(batch.users)
            batch_dict = {
                "id": batch.id,
                "name": batch.name,
                "telegram_chat_id": batch.telegram_chat_id,
                "user_count": user_count
            }
            batch_list.append(batch_dict)
        
        return JSONResponse({
            "success": True,
            "data": batch_list
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/batches/{batch_id}")
async def get_batch_detail(batch_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific batch"""
    try:
        batch = crud.get_batch_by_id(db, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        batch_data = {
            "id": batch.id,
            "name": batch.name,
            "telegram_chat_id": batch.telegram_chat_id,
            "users": [
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone
                }
                for user in batch.users
            ]
        }
        
        return JSONResponse({
            "success": True,
            "data": batch_data
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/batches")
async def create_batch(batch_create: schemas.BatchCreate, db: Session = Depends(get_db)):
    """Create a new batch"""
    try:
        batch = crud.create_batch(db, batch_create)
        
        return JSONResponse({
            "success": True,
            "message": "Batch created successfully",
            "data": {
                "id": batch.id,
                "name": batch.name,
                "telegram_chat_id": batch.telegram_chat_id
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/batches/{batch_id}")
async def update_batch(
    batch_id: int,
    batch_update: schemas.BatchUpdate,
    db: Session = Depends(get_db)
):
    """Update batch information"""
    try:
        batch = crud.get_batch_by_id(db, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        update_data = batch_update.model_dump(exclude_unset=True)
        updated_batch = crud.update_batch(db, batch_id, update_data)
        
        return JSONResponse({
            "success": True,
            "message": "Batch updated successfully",
            "data": {
                "id": updated_batch.id,
                "name": updated_batch.name,
                "telegram_chat_id": updated_batch.telegram_chat_id
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/batches/{batch_id}")
async def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    """Delete a batch"""
    try:
        batch = crud.get_batch_by_id(db, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        crud.delete_batch(db, batch_id)
        
        return JSONResponse({
            "success": True,
            "message": "Batch deleted successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Settings Management Routes ---
@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

@router.get("/api/settings")
async def get_settings(db: Session = Depends(get_db)):
    """Get all settings"""
    try:
        # Start with .env values as defaults
        settings_dict = {
            "RAZORPAY_KEY_ID": os.getenv("RAZORPAY_KEY_ID", ""),
            "RAZORPAY_KEY_SECRET": os.getenv("RAZORPAY_KEY_SECRET", ""),
            "RAZORPAY_WEBHOOK_SECRET": os.getenv("RAZORPAY_WEBHOOK_SECRET", ""),
            "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "TELEGRAM_CHAT_ID_MORNING": os.getenv("TELEGRAM_CHAT_ID_MORNING", ""),
            "TELEGRAM_CHAT_ID_EVENING": os.getenv("TELEGRAM_CHAT_ID_EVENING", ""),
            "SMTP_HOST": os.getenv("SMTP_HOST", ""),
            "SMTP_PORT": os.getenv("SMTP_PORT", ""),
            "SMTP_USER": os.getenv("SMTP_USER", ""),
            "SMTP_PASS": os.getenv("SMTP_PASS", "")
        }
        
        # Override with values from the database
        db_settings = crud.get_settings_as_dict(db)
        settings_dict.update(db_settings)

        return JSONResponse({"success": True, "data": settings_dict})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/settings")
async def update_settings(request: Request, db: Session = Depends(get_db)):
    """Update settings"""
    try:
        form_data = await request.json()
        for key, value in form_data.items():
            if value is not None:
                crud.update_setting(db, key=key, value=value)
        return JSONResponse({"success": True, "message": "Settings updated successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Export Routes ---
@router.get("/api/export/users")
async def export_users(
    format: str = Query("csv", description="Export format: csv or json"),
    db: Session = Depends(get_db)
):
    """Export users data"""
    try:
        users = crud.get_all_users(db, limit=10000)  # Large limit for export
        
        if format.lower() == "csv":
            # Generate CSV content
            csv_content = "ID,Name,Email,Phone,Batch,Payment Count\n"
            for user in users:
                batch_name = user.batch.name if user.batch else "N/A"
                payment_count = len(user.payments)
                csv_content += f"{user.id},{user.name},{user.email},{user.phone},{batch_name},{payment_count}\n"
            
            return JSONResponse({
                "success": True,
                "data": {
                    "format": "csv",
                    "content": csv_content,
                    "filename": f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            })
        else:
            # JSON format
            user_list = []
            for user in users:
                user_dict = {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone,
                    "batch_name": user.batch.name if user.batch else None,
                    "payment_count": len(user.payments)
                }
                user_list.append(user_dict)
            
            return JSONResponse({
                "success": True,
                "data": {
                    "format": "json",
                    "content": user_list,
                    "filename": f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/export/payments")
async def export_payments(
    format: str = Query("csv", description="Export format: csv or json"),
    db: Session = Depends(get_db)
):
    """Export payments data"""
    try:
        payments = crud.get_all_payments(db, limit=10000)  # Large limit for export
        
        if format.lower() == "csv":
            # Generate CSV content
            csv_content = "ID,Payment ID,Order ID,Amount,Currency,Status,User Name,User Email,Batch,Created At\n"
            for payment in payments:
                user_name = payment.user.name if payment.user else "N/A"
                user_email = payment.user.email if payment.user else "N/A"
                batch_name = payment.user.batch.name if payment.user and payment.user.batch else "N/A"
                created_at = payment.created_at.strftime('%Y-%m-%d %H:%M:%S') if payment.created_at else "N/A"
                
                csv_content += f"{payment.id},{payment.razorpay_payment_id},{payment.razorpay_order_id},{payment.amount},{payment.currency},{payment.status},{user_name},{user_email},{batch_name},{created_at}\n"
            
            return JSONResponse({
                "success": True,
                "data": {
                    "format": "csv",
                    "content": csv_content,
                    "filename": f"payments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            })
        else:
            # JSON format
            payment_list = []
            for payment in payments:
                payment_dict = {
                    "id": payment.id,
                    "razorpay_payment_id": payment.razorpay_payment_id,
                    "razorpay_order_id": payment.razorpay_order_id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "status": payment.status,
                    "user_name": payment.user.name if payment.user else None,
                    "user_email": payment.user.email if payment.user else None,
                    "batch_name": payment.user.batch.name if payment.user and payment.user.batch else None,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None
                }
                payment_list.append(payment_dict)
            
            return JSONResponse({
                "success": True,
                "data": {
                    "format": "json",
                    "content": payment_list,
                    "filename": f"payments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 