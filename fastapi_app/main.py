import os
import razorpay
import datetime 
import requests
import aiosmtplib
import hmac
import hashlib
import uuid
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio

from . import crud, models, schemas
from .database import SessionLocal, engine, get_db
from .db_setup import create_db_and_tables
from .admin.router import router as admin_router
from .email_template import get_email_template

load_dotenv()

# Create database and tables
create_db_and_tables()

app = FastAPI()

# Mount the admin router
app.include_router(admin_router)

# Mount static files
app.mount("/public", StaticFiles(directory="fastapi_app/public"), name="public")

# --- Helper Functions ---
def get_app_settings(db: Session = Depends(get_db)):
    """Dependency to get settings from DB with fallback to .env"""
    settings = {}
    
    # Load from .env first as a fallback
    keys = [
        "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET",
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID_MORNING", "TELEGRAM_CHAT_ID_EVENING",
        "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"
    ]
    for key in keys:
        settings[key] = os.getenv(key)
        
    # Override with settings from DB
    db_settings = crud.get_settings_as_dict(db)
    settings.update(db_settings)
    
    return settings

def get_razorpay_client(settings: dict = Depends(get_app_settings)):
    """Dependency to get an initialized Razorpay client"""
    key_id = settings.get("RAZORPAY_KEY_ID")
    key_secret = settings.get("RAZORPAY_KEY_SECRET")
    
    if not key_id or not key_secret:
        raise HTTPException(status_code=500, detail="Razorpay credentials not configured")
        
    return razorpay.Client(auth=(key_id, key_secret))

async def generate_telegram_invite(chat_id: str, settings: dict):
    bot_token = settings.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise Exception("Telegram bot token not configured")
        
    url = f"https://api.telegram.org/bot{bot_token}/createChatInviteLink"
    payload = {"chat_id": chat_id, "member_limit": 1}
    response = requests.post(url, json=payload)
    data = response.json()
    
    if not data.get("ok"):
        raise Exception(f"Telegram error: {data.get('description')}")
    return data["result"]["invite_link"]

async def send_email(to: str, invite_link: str, batch: str, settings: dict, user_name: str = None, payment_id: str = None):
    smtp_user = settings.get("SMTP_USER")
    smtp_pass = settings.get("SMTP_PASS")
    smtp_host = settings.get("SMTP_HOST")
    smtp_port = int(settings.get("SMTP_PORT", 465))
    print(f" this is the invite link {invite_link}")
    if not all([smtp_user, smtp_pass, smtp_host]):
        raise Exception("SMTP settings are not fully configured")
        
    message = MIMEMultipart("alternative")
    message["Subject"] = f"🎉 Welcome to TopG Traders - Your {batch.capitalize()} Trading Course Access"
    message["From"] = f'"TopG Traders" <{smtp_user}>'
    message["To"] = to

    # Use the beautiful email template
    html_content = get_email_template(
        user_name=user_name or "Trader",
        batch_name=batch,
        invite_link=invite_link,
        payment_id=payment_id
    )
    
    message.attach(MIMEText(html_content, "html"))

    await aiosmtplib.send(
        message,
        hostname=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_pass,
        use_tls=True
    )

def verify_signature(body: bytes, signature: str, secret: str):
    if not secret:
        return False
    generated_signature = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(generated_signature, signature)

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("fastapi_app/public/index.html")

@app.get("/success.html", response_class=HTMLResponse)
async def read_success():
    return FileResponse("fastapi_app/public/success.html")

@app.post("/create-order")
async def create_order(
    order_request: schemas.OrderRequest, 
    db: Session = Depends(get_db),
    settings: dict = Depends(get_app_settings),
    razorpay_client: razorpay.Client = Depends(get_razorpay_client)
):
    try:
        order_data = {
            "amount": order_request.amount,
            "currency": "INR",
            "receipt": f"order_{datetime.datetime.now().timestamp()}_{order_request.batchType}",
            "notes": {
                "batch_type": order_request.batchType,
                "customer_name": order_request.name,
                "customer_email": order_request.email,
                "customer_phone": order_request.phone
            }
        }
        order = razorpay_client.order.create(data=order_data)

        # Pre-create user and batch, and generate invite link
        batch = crud.get_batch_by_name(db, name=order_request.batchType)
        if not batch:
            chat_id_key = f"TELEGRAM_CHAT_ID_{order_request.batchType.upper()}"
            chat_id = settings.get(chat_id_key)
            if not chat_id:
                raise HTTPException(status_code=500, detail=f"Telegram chat ID for batch '{order_request.batchType}' not configured")
            batch = crud.create_batch(db, schemas.BatchCreate(name=order_request.batchType, telegram_chat_id=chat_id))

        user = crud.get_user_by_email(db, email=order_request.email)
        if not user:
            # Generate invite link for new user
            invite_link = await generate_telegram_invite(batch.telegram_chat_id, settings)
            user_data = schemas.UserCreate(
                name=order_request.name,
                email=order_request.email,
                phone=order_request.phone,
                invite_link=invite_link
            )
            user = crud.create_user(db, user_data, batch_id=batch.id)
        elif not user.invite_link or user.batch_id != batch.id:
            # If user exists but has no link, or is changing batches, generate a new one.
            invite_link = await generate_telegram_invite(batch.telegram_chat_id, settings)
            user = crud.update_user(db, user_id=user.id, user_data={"invite_link": invite_link, "batch_id": batch.id})

        return JSONResponse({
            "success": True,
            "order_id": order["id"],
            "key_id": settings.get("RAZORPAY_KEY_ID"),
            "amount": order["amount"],
            "currency": order["currency"]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_payment_and_send_email(request_id: str, user_id: int, payment_id: str, batch_type: str, email_to: str, settings: dict):
    """
    This background task handles the core logic of sending the email after a
    successful payment. It is responsible for releasing the processing lock
    acquired by the webhook.
    """
    print(f"BG_TASK {request_id}/{payment_id}: Starting background task.")
    
    # ✅ IMMEDIATE check: Is this payment already processed?
    db_immediate = SessionLocal()
    try:
        immediate_payment = crud.get_payment_by_payment_id(db_immediate, payment_id)
        if immediate_payment and immediate_payment.email_sent:
            print(f"BG_TASK {request_id}/{payment_id}: IMMEDIATE ABORT - Email already sent for this payment!")
            return
    finally:
        db_immediate.close()
    
    db_bg = SessionLocal()
    email_sent_flag = False
    try:
        # Re-fetch payment within the session to ensure we have the latest data
        payment_bg = crud.get_payment_by_payment_id(db_bg, payment_id)
        
        if not payment_bg or not payment_bg.user:
            print(f"BG_TASK {request_id}/{payment_id}: User or Payment not found. Aborting.")
            return

        print(f"BG_TASK {request_id}/{payment_id}: Payment status='{payment_bg.status}', email_sent={payment_bg.email_sent}")

        # ✅ Final idempotency check: Has the email already been sent for this payment?
        if payment_bg.email_sent:
            print(f"BG_TASK {request_id}/{payment_id}: Email already sent for this payment. Aborting.")
            return

        # Safety check: ensure we don't re-process a completed payment.
        if payment_bg.status == "completed":
            print(f"BG_TASK {request_id}/{payment_id}: Payment is already completed. Aborting.")
            return

        if not payment_bg.user.invite_link:
            print(f"BG_TASK {request_id}/{payment_id}: FATAL - Invite link not found for user {payment_bg.user.id}.")
            crud.update_payment_status(db_bg, payment_id=payment_id, status="failed")
            return
        
        invite_link = payment_bg.user.invite_link
        print(f"BG_TASK {request_id}/{payment_id}: Using invite link: {invite_link[:50]}...")
        
        # ✅ CRITICAL: Double-check email_sent flag right before sending
        db_bg.refresh(payment_bg)
        if payment_bg.email_sent:
            print(f"BG_TASK {request_id}/{payment_id}: Email already sent (double-check). Aborting.")
            return
        
        print(f"BG_TASK {request_id}/{payment_id}: Attempting to send email to {payment_bg.user.email}.")
        await send_email(
            to=payment_bg.user.email, 
            invite_link=invite_link, 
            batch=payment_bg.user.batch.name, 
            settings=settings,
            user_name=payment_bg.user.name,
            payment_id=payment_id
        )
        email_sent_flag = True
        print(f"BG_TASK {request_id}/{payment_id}: Email send successful.")
        
        # ✅ Atomically mark payment as completed AND email as sent.
        crud.update_payment_status(db_bg, payment_id=payment_bg.razorpay_payment_id, status="completed", email_sent=True)
        print(f"BG_TASK {request_id}/{payment_id}: Payment marked as completed and email_sent=True")

    except Exception as e:
        db_bg.rollback()
        if not email_sent_flag:
            # If email was not sent, it's safe to mark as failed for a potential retry.
            print(f"BG_TASK {request_id}/{payment_id}: Email was NOT sent. Marking as failed due to error: {e}")
            crud.update_payment_status(db_bg, payment_id=payment_id, status="failed")
        else:
            # Email was sent, but a subsequent DB update failed. Log critically.
            # The status will remain 'processing', preventing re-sends on webhook retries.
            print(f"BG_TASK {request_id}/{payment_id}: CRITICAL - Email sent, but DB update failed: {e}")
        print(f"BG_TASK {request_id}/{payment_id}: Error processing payment: {e}")
    finally:
        print(f"BG_TASK {request_id}/{payment_id}: Releasing processing lock.")
        crud.remove_processing_lock(db_bg, payment_id)
        db_bg.close()
        print(f"BG_TASK {request_id}/{payment_id}: Background task finished.")


@app.post("/webhook")
async def webhook(
    request: Request, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    settings: dict = Depends(get_app_settings),
    razorpay_client: razorpay.Client = Depends(get_razorpay_client)
):
    request_id = uuid.uuid4().hex[:6]
    raw_body = await request.body()
    signature = request.headers.get("x-razorpay-signature")
    webhook_secret = settings.get("RAZORPAY_WEBHOOK_SECRET")
    
    payment_id_for_logging = "N/A"
    try:
        body = await request.json()
        payment_id_for_logging = body.get("payload", {}).get("payment", {}).get("entity", {}).get("id", "N/A")
    except Exception:
        body = {} # In case of JSON decode error
        
    print(f"WEBHOOK {request_id}/{payment_id_for_logging}: Received request.")

    if not verify_signature(raw_body, signature, webhook_secret):
        print(f"WEBHOOK {request_id}/{payment_id_for_logging}: Invalid signature.")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event = body.get("event")

    if event == "payment.captured":
        payment_entity = body["payload"]["payment"]["entity"]
        payment_id = payment_entity["id"]
        
        print(f"WEBHOOK {request_id}/{payment_id}: Event 'payment.captured'. Attempting to acquire lock.")
        lock = models.ProcessingLock(payment_id=payment_id)
        db.add(lock)
        try:
            db.commit()
            print(f"WEBHOOK {request_id}/{payment_id}: Lock acquired successfully.")
        except IntegrityError:
            db.rollback()
            print(f"WEBHOOK {request_id}/{payment_id}: Lock already exists. Aborting.")
            return JSONResponse({"status": "ok", "message": "Already processing."})

        try:
            # --- Idempotency Check (after acquiring lock) ---
            existing_payment = crud.get_payment_by_payment_id(db, payment_id=payment_id)
            if existing_payment and existing_payment.status == "completed":
                print(f"WEBHOOK {request_id}/{payment_id}: Payment already completed. Releasing lock and aborting.")
                crud.remove_processing_lock(db, payment_id)
                return JSONResponse({"status": "ok", "message": "Payment already completed."})

            # --- Get data and prepare for background task ---
            order_id = payment_entity["order_id"]
            email = payment_entity["email"]
            amount = payment_entity["amount"] / 100
            currency = payment_entity["currency"]
            order = razorpay_client.order.fetch(order_id)
            batch_type = order["notes"]["batch_type"]

            user = crud.get_user_by_email(db, email=email)
            if not user:
                print(f"WEBHOOK {request_id}/{payment_id}: CRITICAL - User not found for email {email}. Releasing lock.")
                crud.remove_processing_lock(db, payment_id)
                return JSONResponse({"status": "ok", "message": "User not found."})

            # --- Create/Update payment record to 'processing' ---
            if not existing_payment:
                payment_data = schemas.PaymentCreate(
                    razorpay_payment_id=payment_id,
                    razorpay_order_id=order_id,
                    amount=amount,
                    currency=currency,
                    status="processing"
                )
                crud.create_payment(db, payment_data, user_id=user.id)
            else:
                crud.update_payment_status(db, payment_id=payment_id, status="processing")
            
            print(f"WEBHOOK {request_id}/{payment_id}: Adding payment processing to background tasks.")
            background_tasks.add_task(process_payment_and_send_email, request_id, user.id, payment_id, batch_type, email, settings)

        except Exception as e:
            print(f"WEBHOOK {request_id}/{payment_id}: Unhandled error after lock acquisition: {e}. Releasing lock.")
            db.rollback()
            crud.remove_processing_lock(db, payment_id)
            raise HTTPException(status_code=500, detail="Internal Server Error in webhook.")

    return JSONResponse({"status": "ok"})

@app.post("/get-invite-link")
async def get_invite_link(req: Request, db: Session = Depends(get_db)):
    data = await req.json()
    payment_id = data.get("paymentId")
    
    # Poll for up to 10 seconds to wait for the webhook to process
    for _ in range(5):
        db.expire_all() # Ensure we get the latest from the DB
        payment = crud.get_payment_by_payment_id(db, payment_id=payment_id)
        if payment and payment.user and payment.user.invite_link:
            return JSONResponse({
                "success": True,
                "inviteLink": payment.user.invite_link,
                "batchType": payment.user.batch.name,
                "message": "Retrieved stored invite link",
                "data": {
                    "success": True,
                    "inviteLink": payment.user.invite_link
                }
            })
        await asyncio.sleep(2) # Wait 2 seconds before retrying

    return JSONResponse({
        "success": False,
        "error": "Invite link not found. Please check your email for the invite link."
    }, status_code=404)

@app.get("/retrieve-invite-link/{payment_id}")
async def retrieve_invite_link(payment_id: str, db: Session = Depends(get_db)):
    """
    Simple endpoint to retrieve existing invite link from database.
    No polling, no processing - just fetch what's already there.
    """
    payment = crud.get_payment_by_payment_id(db, payment_id=payment_id)
    
    if payment and payment.user and payment.user.invite_link:
        return JSONResponse({
            "success": True,
            "inviteLink": payment.user.invite_link,
            "batchType": payment.user.batch.name,
            "status": payment.status,
            "message": "Invite link retrieved successfully"
        })
    else:
        status = "not_found"
        if payment:
            status = payment.status
        
        return JSONResponse({
            "success": False,
            "error": "Invite link not available yet. Please check your email.",
            "status": status
        }, status_code=404)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/status")
def get_status(settings: dict = Depends(get_app_settings)):
    return {
        "server": "running",
        "timestamp": datetime.datetime.now().isoformat(),
        "environment": {
            "razorpay": {
                "keyId": bool(settings.get("RAZORPAY_KEY_ID")),
            },
            "telegram": {
                "botToken": bool(settings.get("TELEGRAM_BOT_TOKEN")),
                "morningChatId": bool(settings.get("TELEGRAM_CHAT_ID_MORNING")),
                "eveningChatId": bool(settings.get("TELEGRAM_CHAT_ID_EVENING"))
            },
            "smtp": {
                "host": bool(settings.get("SMTP_HOST")),
                "port": bool(settings.get("SMTP_PORT")),
                "user": bool(settings.get("SMTP_USER"))
            }
        }
    }

