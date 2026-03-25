"""
Notifier: Send email and SMS alerts for near-expiry and low-stock medicines.
"""
import os
import smtplib
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from db_config import DB_PATH
from operations import get_near_expiry_medicines, get_low_stock_medicines, get_expired_medicines

# Load environment variables from .env
load_dotenv()

# Email Credentials (from .env)
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

# Twilio Credentials (from .env)
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
RECEIVER_PHONE_NUMBER = os.getenv("RECEIVER_PHONE_NUMBER")

# Configuration
EXPIRY_LEAD_DAYS = int(os.getenv("EXPIRY_LEAD_DAYS", 180))


def get_sms_config_status():
    """Check if SMS is properly configured."""
    load_dotenv(override=True)
    twilio_sid = os.getenv("TWILIO_SID", "").strip()
    twilio_auth = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    twilio_phone = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
    receiver_phone = os.getenv("RECEIVER_PHONE_NUMBER", "").strip()
    
    missing = []
    if not twilio_sid:
        missing.append("TWILIO_SID")
    if not twilio_auth:
        missing.append("TWILIO_AUTH_TOKEN")
    if not twilio_phone:
        missing.append("TWILIO_PHONE_NUMBER")
    if not receiver_phone:
        missing.append("RECEIVER_PHONE_NUMBER")
    
    return {
        "configured": len(missing) == 0,
        "missing": missing,
        "twilio_sid": twilio_sid[:10] + "..." if twilio_sid else "Not set",
        "twilio_phone": twilio_phone if twilio_phone else "Not set",
        "receiver_phone": receiver_phone if receiver_phone else "Not set"
    }


def send_email_alert(subject, message):
    """Send email alert."""
    # Reload environment variables to get latest settings
    load_dotenv(override=True)
    email_sender = os.getenv("EMAIL_SENDER", "").strip()
    email_password = os.getenv("EMAIL_PASSWORD", "").strip().replace(" ", "")
    email_receiver = os.getenv("EMAIL_RECEIVER", "").strip()
    
    if not email_sender or not email_password or not email_receiver:
        print("Email credentials not configured. Skipping email alert.")
        return False
    
    try:
        msg = MIMEMultipart()
        msg["From"] = email_sender
        msg["To"] = email_receiver
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.sendmail(email_sender, email_receiver, msg.as_string())

        print(f"✓ Email alert sent: {subject}")
        return True
    except Exception as e:
        print(f"✗ Email alert failed: {e}")
        return False


def send_sms_alert(message):
    """Send SMS alert via Twilio."""
    if not TWILIO_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER or not RECEIVER_PHONE_NUMBER:
        print("Twilio credentials not configured. Skipping SMS alert.")
        return False
    
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        sms_body = message[:1500] if len(message) > 1500 else message
        msg = client.messages.create(body=sms_body, from_=TWILIO_PHONE_NUMBER, to=RECEIVER_PHONE_NUMBER)
        print(f"✓ SMS alert sent: {msg.sid}")
        return True
    except Exception as e:
        print(f"✗ SMS alert failed: {e}")
        return False


def check_and_notify():
    """Check for expiry and low-stock medicines, then send alerts."""
    print(f"\n{'='*50}")
    print(f"Checking alerts at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # Get alerts
    expired = get_expired_medicines()
    near_expiry = get_near_expiry_medicines(EXPIRY_LEAD_DAYS)
    low_stock = get_low_stock_medicines()

    # Categorize near-expiry by urgency (based on days remaining)
    today = datetime.now().date()
    critical_expiry = []  # 0-30 days
    warning_expiry = []   # 31-90 days
    notice_expiry = []    # 91+ days

    for item in near_expiry:
        try:
            expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
            days_remaining = (expiry_date - today).days
            
            if days_remaining <= 30:
                critical_expiry.append({**item, 'days_remaining': days_remaining})
            elif days_remaining <= 90:
                warning_expiry.append({**item, 'days_remaining': days_remaining})
            else:
                notice_expiry.append({**item, 'days_remaining': days_remaining})
        except:
            notice_expiry.append(item)

    # Build alert message
    alerts = []

    if expired:
        print(f"🔴 Found {len(expired)} EXPIRED medicines")
        alerts.append(f"\n🔴 EXPIRED MEDICINES - USE IMMEDIATELY ({len(expired)}):")
        for item in expired:
            alerts.append(f"  - {item['name']} (Batch: {item['batch_number']}, Expiry: {item['expiry_date']}, Qty: {item['quantity']})")

    if critical_expiry:
        print(f"🔴 Found {len(critical_expiry)} CRITICAL medicines (expiring within 30 days)")
        alerts.append(f"\n🔴 CRITICAL - EXPIRING WITHIN 30 DAYS ({len(critical_expiry)}):")
        for item in sorted(critical_expiry, key=lambda x: x['days_remaining']):
            alerts.append(f"  - {item['name']} (Batch: {item['batch_number']}, Expiry: {item['expiry_date']}, Days Left: {item['days_remaining']}, Qty: {item['quantity']})")

    if warning_expiry:
        print(f"🟡 Found {len(warning_expiry)} WARNING medicines (expiring in 31-90 days)")
        alerts.append(f"\n🟡 WARNING - EXPIRING IN 31-90 DAYS ({len(warning_expiry)}):")
        for item in sorted(warning_expiry, key=lambda x: x['days_remaining']):
            alerts.append(f"  - {item['name']} (Batch: {item['batch_number']}, Expiry: {item['expiry_date']}, Days Left: {item['days_remaining']}, Qty: {item['quantity']})")

    if notice_expiry:
        print(f"🔵 Found {len(notice_expiry)} NOTICE medicines (expiring in 91+ days)")
        alerts.append(f"\n🔵 NOTICE - EXPIRING IN 91+ DAYS ({len(notice_expiry)}):")
        for item in sorted(notice_expiry, key=lambda x: x['days_remaining']):
            alerts.append(f"  - {item['name']} (Batch: {item['batch_number']}, Expiry: {item['expiry_date']}, Days Left: {item['days_remaining']}, Qty: {item['quantity']})")

    if low_stock:
        print(f"📉 Found {len(low_stock)} LOW-STOCK medicines")
        alerts.append(f"\n📉 LOW-STOCK MEDICINES ({len(low_stock)}):")
        for item in low_stock:
            alerts.append(f"  - {item['name']} (Current: {item['total_stock']}, Threshold: {item['low_stock_threshold']})")

    if not alerts:
        print("✓ No alerts to send. All medicines are in good condition!\n")
        return

    # Send alerts
    message_body = "\n".join(alerts)
    
    print("\nSending alerts...")
    email_sent = send_email_alert("PharmaAlert: Medicine Stock Alert", message_body)
    sms_sent = send_sms_alert(message_body)

    if email_sent or sms_sent:
        # Log to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO alert_history (alert_type, message) VALUES (?, ?)",
            ("combined", message_body)
        )
        conn.commit()
        conn.close()
        print("✓ Alert logged to database.\n")
    else:
        print("✗ No alerts sent (credentials missing).\n")


if __name__ == "__main__":
    check_and_notify()

