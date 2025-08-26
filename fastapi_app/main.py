import os
import razorpay
import requests
import aiosmtplib
import hmac
import hashlib
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio

from . import crud, models, schemas
from .database import SessionLocal, engine, get_db
from .db_setup import create_db_and_tables
from .admin.router import router as admin_router

load_dotenv()

# Create database and tables
create_db_and_tables()

app = FastAPI()

# Mount the admin router
app.include_router(admin_router)

# Mount static files
app.mount("/public", StaticFiles(directory="fastapi_app/public"), name="public")

# --- Environment Variables ---
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID_MORNING = os.getenv("TELEGRAM_CHAT_ID_MORNING")
TELEGRAM_CHAT_ID_EVENING = os.getenv("TELEGRAM_CHAT_ID_EVENING")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# --- Helper Functions ---

async def generate_telegram_invite(chat_id: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/createChatInviteLink"
    payload = {
        "chat_id": chat_id,
        "member_limit": 1
    }
    response = requests.post(url, json=payload)
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Telegram error: {data.get('description')}")
    return data["result"]["invite_link"]

async def send_email(to: str, invite_link: str, batch: str):
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Your Telegram Invite Link ({batch} batch)"
    message["From"] = f'"{batch.capitalize()} Batch Access" <{SMTP_USER}>'
    message["To"] = to

    html = f"""
        <p>Hi,</p>
        <p>Thanks for joining the <b>{batch}</b> batch! Here's your one-time invite link:</p>
        <p><a href="{invite_link}" target="_blank" rel="noreferrer">{invite_link}</a></p>
        <p><small>This link is valid for 24 hours and can be used once.</small></p>
    """
    message.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASS,
        use_tls=True
    )

def verify_signature(body: bytes, signature: str, secret: str):
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
async def create_order(order_request: schemas.OrderRequest, db: Session = Depends(get_db)):
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

        # Pre-create user and batch if they don't exist
        batch = crud.get_batch_by_name(db, name=order_request.batchType)
        if not batch:
            chat_id = TELEGRAM_CHAT_ID_MORNING if order_request.batchType == "morning" else TELEGRAM_CHAT_ID_EVENING
            batch = crud.create_batch(db, schemas.BatchCreate(name=order_request.batchType, telegram_chat_id=chat_id))

        user = crud.get_user_by_email(db, email=order_request.email)
        if not user:
            user = crud.create_user(db, schemas.UserCreate(name=order_request.name, email=order_request.email, phone=order_request.phone), batch_id=batch.id)

        return JSONResponse({
            "success": True,
            "order_id": order["id"],
            "key_id": RAZORPAY_KEY_ID,
            "amount": order["amount"],
            "currency": order["currency"]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_payment_and_send_email(user_id: int, payment_id: str, batch_type: str, email_to: str):
    db_bg = SessionLocal()
    try:
        user_bg = db_bg.query(models.User).filter(models.User.id == user_id).first()
        payment_bg = crud.get_payment_by_payment_id(db_bg, payment_id)
        
        if not user_bg or not payment_bg:
            crud.update_payment_status(db_bg, payment_id=payment_id, status="failed")
            return

        # Only generate link if it doesn't exist
        if not payment_bg.invite_link:
            chat_id = user_bg.batch.telegram_chat_id
            invite_link = await generate_telegram_invite(chat_id)
            crud.update_payment_invite_link(db_bg, payment_id=payment_bg.razorpay_payment_id, invite_link=invite_link)
        else:
            invite_link = payment_bg.invite_link
        
        # Attempt to send email
        await send_email(to=email_to, invite_link=invite_link, batch=batch_type)
        
        # If successful, mark as completed
        crud.update_payment_status(db_bg, payment_id=payment_bg.razorpay_payment_id, status="completed")

    except Exception as e:
        # On failure, mark as failed to allow for potential retries
        crud.update_payment_status(db_bg, payment_id=payment_id, status="failed")
        print(f"Error processing payment {payment_id}: {e}")
    finally:
        db_bg.close()

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    raw_body = await request.body()
    signature = request.headers.get("x-razorpay-signature")

    if not verify_signature(raw_body, signature, RAZORPAY_WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="Invalid signature")

    body = await request.json()
    event = body.get("event")

    if event == "payment.captured":
        payment_entity = body["payload"]["payment"]["entity"]
        payment_id = payment_entity["id"]
        
        # --- Robust Idempotency Check ---
        db.expire_all() # Ensure we have the latest from the DB
        existing_payment = crud.get_payment_by_payment_id(db, payment_id=payment_id)

        # If already completed or currently processing, do nothing.
        if existing_payment and existing_payment.status in ["processing", "completed"]:
            return JSONResponse({"status": "ok", "message": f"Payment {payment_id} is already {existing_payment.status}."})

        # --- Mark as Processing and Start Task ---
        order_id = payment_entity["order_id"]
        email = payment_entity["email"]
        amount = payment_entity["amount"] / 100
        currency = payment_entity["currency"]
        order = razorpay_client.order.fetch(order_id)
        batch_type = order["notes"]["batch_type"]

        user = crud.get_user_by_email(db, email=email)
        if user:
            # If payment doesn't exist, create it.
            if not existing_payment:
                payment_data = schemas.PaymentCreate(
                    razorpay_payment_id=payment_id,
                    razorpay_order_id=order_id,
                    amount=amount,
                    currency=currency,
                    status="processing", # Set to processing
                    invite_link=None
                )
                crud.create_payment(db, payment_data, user_id=user.id)
            else: # If it exists but failed/was pending, mark it as processing now
                crud.update_payment_status(db, payment_id=payment_id, status="processing")
            
            # Launch background task
            background_tasks.add_task(process_payment_and_send_email, user.id, payment_id, batch_type, email)

    return JSONResponse({"status": "ok"})

@app.post("/get-invite-link")
async def get_invite_link(req: Request, db: Session = Depends(get_db)):
    data = await req.json()
    payment_id = data.get("paymentId")
    
    # Poll for up to 10 seconds to wait for the webhook to process
    for _ in range(5):
        db.expire_all() # Ensure we get the latest from the DB
        payment = crud.get_payment_by_payment_id(db, payment_id=payment_id)
        if payment and payment.invite_link:
            return JSONResponse({
                "success": True,
                "inviteLink": payment.invite_link,
                "batchType": payment.user.batch.name,
                "message": "Retrieved stored invite link",
                "data": {
                    "success": True,
                    "inviteLink": payment.invite_link
                }
            })
        await asyncio.sleep(2) # Wait 2 seconds before retrying

    return JSONResponse({
        "success": False,
        "error": "Invite link not found. Please check your email for the invite link."
    }, status_code=404)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/status")
def get_status():
    return {
        "server": "running",
        "timestamp": datetime.datetime.now().isoformat(),
        "environment": {
            "razorpay": {
                "keyId": bool(RAZORPAY_KEY_ID),
            },
            "telegram": {
                "botToken": bool(TELEGRAM_BOT_TOKEN),
                "morningChatId": bool(TELEGRAM_CHAT_ID_MORNING),
                "eveningChatId": bool(TELEGRAM_CHAT_ID_EVENING)
            },
            "smtp": {
                "host": bool(SMTP_HOST),
                "port": bool(SMTP_PORT),
                "user": bool(SMTP_USER)
            }
        }
    }

import datetime 