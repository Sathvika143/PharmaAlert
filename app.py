from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import sqlite3
import io
import os
from datetime import datetime, timedelta
from db_config import DB_PATH
from schema import create_schema
from operations import (
    get_all_medicines, get_medicine, add_medicine, update_medicine, delete_medicine,
    get_batches_by_medicine, add_batch, get_batch,
    receive_stock, issue_stock, get_usage_log,
    get_near_expiry_medicines, get_low_stock_medicines, get_expired_medicines,
    get_dashboard_stats
)
from scheduler import start_scheduler, stop_scheduler
from notifier import check_and_notify
from export_reports import (
    generate_csv_near_expiry, generate_csv_low_stock, generate_csv_expired,
    generate_csv_usage_log, generate_csv_all_medicines
)
from auth import init_users, create_user, get_user_by_id, verify_user_password, log_audit

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this-in-production"

# Ensure core schema exists before auth/scheduler use the database
create_schema(DB_PATH)

# Initialize authentication
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Initialize users table
init_users()

# Create default admin user if not exists
try:
    create_user("admin", "admin123", "admin")
except:
    pass  # User already exists


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))


# ==================== AUTH ROUTES ====================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = verify_user_password(username, password)
        if user:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")
    
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))


# Start scheduler on app startup
start_scheduler()

@app.route("/")
@login_required
def index():
    medicines = get_all_medicines()
    return render_template("index.html", medicines=medicines)


@app.route("/dashboard")
@login_required
def dashboard():
    stats = get_dashboard_stats()
    near_expiry = get_near_expiry_medicines()
    low_stock = get_low_stock_medicines()
    usage_log = get_usage_log(20)
    return render_template("dashboard.html", stats=stats, near_expiry=near_expiry, low_stock=low_stock, usage_log=usage_log)


@app.route("/medicines")
@login_required
def medicines_list():
    medicines = get_all_medicines()
    return render_template("medicines.html", medicines=medicines)


@app.route("/add-medicine", methods=["GET", "POST"])
@login_required
def add_medicine_route():
    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        low_stock_threshold = request.form.get("low_stock_threshold", 50, type=int)
        
        result = add_medicine(name, category, low_stock_threshold)
        if result["success"]:
            log_audit(current_user.id, "ADD", "medicines", result["id"])
            flash("Medicine added successfully!", "success")
            return redirect(url_for("medicines_list"))
        else:
            flash(result["error"], "danger")
    
    return render_template("add_medicine.html")


@app.route("/medicine/<int:medicine_id>")
@login_required
def medicine_detail(medicine_id):
    medicine = get_medicine(medicine_id)
    if not medicine:
        flash("Medicine not found", "danger")
        return redirect(url_for("medicines_list"))
    
    batches = get_batches_by_medicine(medicine_id)
    total_stock = sum(b["quantity"] for b in batches)
    
    return render_template("medicine_detail.html", medicine=medicine, batches=batches, total_stock=total_stock)


@app.route("/medicine/<int:medicine_id>/edit", methods=["GET", "POST"])
@login_required
def edit_medicine(medicine_id):
    medicine = get_medicine(medicine_id)
    if not medicine:
        flash("Medicine not found", "danger")
        return redirect(url_for("medicines_list"))
    
    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        low_stock_threshold = request.form.get("low_stock_threshold", type=int)
        
        result = update_medicine(medicine_id, name, category, low_stock_threshold)
        if result["success"]:
            flash("Medicine updated successfully!", "success")
            return redirect(url_for("medicine_detail", medicine_id=medicine_id))
        else:
            flash(result["error"], "danger")
    
    return render_template("add_medicine.html", medicine=medicine, is_edit=True)


@app.route("/medicine/<int:medicine_id>/delete")
@login_required
def delete_medicine_route(medicine_id):
    result = delete_medicine(medicine_id)
    if result["success"]:
        log_audit(current_user.id, "DELETE", "medicines", medicine_id)
        flash("Medicine deleted successfully!", "success")
    else:
        flash(result["error"], "danger")
    return redirect(url_for("medicines_list"))


@app.route("/medicine/<int:medicine_id>/add-batch", methods=["GET", "POST"])
@login_required
def add_batch_route(medicine_id):
    medicine = get_medicine(medicine_id)
    if not medicine:
        flash("Medicine not found", "danger")
        return redirect(url_for("medicines_list"))
    
    if request.method == "POST":
        batch_number = request.form.get("batch_number")
        expiry_date = request.form.get("expiry_date")
        quantity = request.form.get("quantity", type=int)
        
        result = add_batch(medicine_id, batch_number, expiry_date, quantity)
        if result["success"]:
            log_audit(current_user.id, "ADD", "batches", result["id"])
            flash("Batch added successfully!", "success")
            return redirect(url_for("medicine_detail", medicine_id=medicine_id))
        else:
            flash(result["error"], "danger")
    
    return render_template("add_batch.html", medicine_name=medicine["name"], medicine_id=medicine_id)


@app.route("/batch/<int:batch_id>/receive", methods=["GET", "POST"])
@login_required
def receive_stock_route(batch_id):
    batch = get_batch(batch_id)
    if not batch:
        flash("Batch not found", "danger")
        return redirect(url_for("medicines_list"))
    
    medicine = get_medicine(batch["medicine_id"])
    
    if request.method == "POST":
        quantity = request.form.get("quantity", type=int)
        reason = request.form.get("reason", "Stock received")
        
        result = receive_stock(batch_id, quantity, reason)
        if result["success"]:
            flash(f"Received {quantity} units successfully!", "success")
            return redirect(url_for("medicine_detail", medicine_id=batch["medicine_id"]))
        else:
            flash(result["error"], "danger")
    
    return render_template("stock_operation.html", 
                          operation="receive",
                          medicine_name=medicine["name"],
                          batch_number=batch["batch_number"],
                          current_quantity=batch["quantity"],
                          medicine_id=batch["medicine_id"],
                          batch_id=batch_id)


@app.route("/batch/<int:batch_id>/issue", methods=["GET", "POST"])
@login_required
def issue_stock_route(batch_id):
    batch = get_batch(batch_id)
    if not batch:
        flash("Batch not found", "danger")
        return redirect(url_for("medicines_list"))
    
    medicine = get_medicine(batch["medicine_id"])
    
    if request.method == "POST":
        quantity = request.form.get("quantity", type=int)
        reason = request.form.get("reason", "Stock issued")
        
        result = issue_stock(batch_id, quantity, reason)
        if result["success"]:
            flash(f"Issued {quantity} units successfully!", "success")
            return redirect(url_for("medicine_detail", medicine_id=batch["medicine_id"]))
        else:
            flash(result["error"], "danger")
    
    return render_template("stock_operation.html", 
                          operation="issue",
                          medicine_name=medicine["name"],
                          batch_number=batch["batch_number"],
                          current_quantity=batch["quantity"],
                          medicine_id=batch["medicine_id"],
                          batch_id=batch_id)


@app.route("/batch/<int:batch_id>/delete")
@login_required
def delete_batch_route(batch_id):
    batch = get_batch(batch_id)
    if batch:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM batches WHERE id = ?", (batch_id,))
        conn.commit()
        conn.close()
        log_audit(current_user.id, "DELETE", "batches", batch_id)
        flash("Batch deleted successfully!", "success")
        return redirect(url_for("medicine_detail", medicine_id=batch["medicine_id"]))
    else:
        flash("Batch not found", "danger")
        return redirect(url_for("medicines_list"))

@app.route("/alerts")
@login_required
def alerts():
    near_expiry = get_near_expiry_medicines()
    low_stock = get_low_stock_medicines()
    expired = get_expired_medicines()
    return render_template("alerts.html", near_expiry=near_expiry, low_stock=low_stock, expired=expired)


@app.route("/manual-check", methods=["POST"])
@login_required
def manual_check():
    """Manually trigger expiry and low-stock checks."""
    try:
        check_and_notify()
        return jsonify({"success": True, "message": "Checks completed and alerts sent!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/cron-check", methods=["GET", "POST"])
def cron_check():
    """Trigger checks from an external scheduler using a shared secret."""
    cron_secret = os.getenv("CRON_SECRET", "").strip()
    provided = request.args.get("token", "").strip() or request.headers.get("X-Cron-Token", "").strip()

    if not cron_secret:
        return jsonify({"success": False, "error": "CRON_SECRET is not configured"}), 503

    if provided != cron_secret:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        check_and_notify()
        return jsonify({"success": True, "message": "Scheduled checks completed"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== REPORTS ====================

@app.route("/reports")
@login_required
def reports():
    """Reports overview page."""
    return render_template("reports.html")


@app.route("/export/near-expiry")
@login_required
def export_near_expiry():
    """Export near-expiry medicines as CSV."""
    csv_data = generate_csv_near_expiry()
    return send_file(
        io.BytesIO(csv_data.encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"near_expiry_{datetime.now().strftime('%Y%m%d')}.csv"
    )


@app.route("/export/low-stock")
@login_required
def export_low_stock():
    """Export low-stock medicines as CSV."""
    csv_data = generate_csv_low_stock()
    return send_file(
        io.BytesIO(csv_data.encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"low_stock_{datetime.now().strftime('%Y%m%d')}.csv"
    )


@app.route("/export/expired")
@login_required
def export_expired():
    """Export expired medicines as CSV."""
    csv_data = generate_csv_expired()
    return send_file(
        io.BytesIO(csv_data.encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"expired_{datetime.now().strftime('%Y%m%d')}.csv"
    )


@app.route("/export/usage-log")
@login_required
def export_usage_log():
    """Export usage log as CSV."""
    csv_data = generate_csv_usage_log()
    return send_file(
        io.BytesIO(csv_data.encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"usage_log_{datetime.now().strftime('%Y%m%d')}.csv"
    )


@app.route("/export/all-medicines")
@login_required
def export_all_medicines():
    """Export all medicines inventory as CSV."""
    csv_data = generate_csv_all_medicines()
    return send_file(
        io.BytesIO(csv_data.encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"medicines_inventory_{datetime.now().strftime('%Y%m%d')}.csv"
    )


# ==================== SETTINGS ====================

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    """Email notification settings page."""
    if request.method == "POST":
        # Get form data
        email_sender = request.form.get("email_sender", "").strip()
        email_password = request.form.get("email_password", "").strip()
        email_receiver = request.form.get("email_receiver", "").strip()
        expiry_lead_days = request.form.get("expiry_lead_days", "180").strip()
        
        # Read current .env file
        env_path = ".env"
        env_lines = []
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add environment variables
        def update_or_add_env_var(lines, key, value):
            found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f'{key}="{value}"\n'
                    found = True
                    break
            if not found:
                lines.append(f'{key}="{value}"\n')
            return lines
        
        env_lines = update_or_add_env_var(env_lines, "EMAIL_SENDER", email_sender)
        env_lines = update_or_add_env_var(env_lines, "EMAIL_PASSWORD", email_password)
        env_lines = update_or_add_env_var(env_lines, "EMAIL_RECEIVER", email_receiver)
        env_lines = update_or_add_env_var(env_lines, "EXPIRY_LEAD_DAYS", expiry_lead_days)
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        # Update environment variables for current session
        os.environ["EMAIL_SENDER"] = email_sender
        os.environ["EMAIL_PASSWORD"] = email_password
        os.environ["EMAIL_RECEIVER"] = email_receiver
        os.environ["EXPIRY_LEAD_DAYS"] = expiry_lead_days
        
        flash("Email settings saved successfully! Restart the app for changes to take full effect.", "success")
        return redirect(url_for("settings"))
    
    # Read current settings from environment
    current_settings = {
        "email_sender": os.getenv("EMAIL_SENDER", ""),
        "email_password": os.getenv("EMAIL_PASSWORD", ""),
        "email_receiver": os.getenv("EMAIL_RECEIVER", ""),
        "expiry_lead_days": os.getenv("EXPIRY_LEAD_DAYS", "180"),
    }
    
    return render_template("settings.html", settings=current_settings)


@app.route("/test-email", methods=["POST"])
@login_required
def test_email():
    """Test email notification."""
    try:
        from notifier import send_email_alert
        success = send_email_alert(
            "PharmaAlert Test Email",
            "This is a test email from PharmaAlert. If you received this, your email notifications are working correctly!"
        )
        if success:
            return jsonify({"success": True, "message": "Test email sent successfully! Check your inbox."})
        else:
            return jsonify({"success": False, "message": "Failed to send test email. Check your email settings."}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@app.route("/test-sms", methods=["POST"])
@login_required
def test_sms():
    """Test SMS notification via Twilio."""
    try:
        from notifier import send_sms_alert, get_sms_config_status
        
        # Check if SMS is configured
        config_status = get_sms_config_status()
        if not config_status["configured"]:
            return jsonify({"success": False, "message": f"SMS not configured. Missing: {', '.join(config_status['missing'])}"}), 400
        
        test_message = "🔔 PharmaAlert Test SMS: If you received this, your SMS notifications are working correctly!"
        success = send_sms_alert(test_message)
        
        if success:
            return jsonify({"success": True, "message": "Test SMS sent successfully! Check your phone."})
        else:
            return jsonify({"success": False, "message": "Failed to send test SMS. Check your Twilio credentials."}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@app.route("/sms-settings", methods=["GET", "POST"])
@login_required
def sms_settings():
    """SMS notification settings page."""
    if request.method == "POST":
        twilio_sid = request.form.get("twilio_sid", "").strip()
        twilio_auth = request.form.get("twilio_auth_token", "").strip()
        twilio_phone = request.form.get("twilio_phone_number", "").strip()
        receiver_phone = request.form.get("receiver_phone_number", "").strip()
        
        # Read and update .env file
        env_path = ".env"
        env_lines = []
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        def update_or_add_env_var(lines, key, value):
            found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f'{key}="{value}"\n'
                    found = True
                    break
            if not found:
                lines.append(f'{key}="{value}"\n')
            return lines
        
        env_lines = update_or_add_env_var(env_lines, "TWILIO_SID", twilio_sid)
        env_lines = update_or_add_env_var(env_lines, "TWILIO_AUTH_TOKEN", twilio_auth)
        env_lines = update_or_add_env_var(env_lines, "TWILIO_PHONE_NUMBER", twilio_phone)
        env_lines = update_or_add_env_var(env_lines, "RECEIVER_PHONE_NUMBER", receiver_phone)
        
        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        # Reload environment
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        flash("SMS settings saved successfully! Restart the app for changes to take effect.", "success")
        return redirect(url_for("sms_settings"))
    
    # Get current SMS status and settings
    from notifier import get_sms_config_status
    sms_status = get_sms_config_status()
    current_settings = {
        "twilio_sid": os.getenv("TWILIO_SID", ""),
        "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
        "twilio_phone_number": os.getenv("TWILIO_PHONE_NUMBER", ""),
        "receiver_phone_number": os.getenv("RECEIVER_PHONE_NUMBER", ""),
    }
    
    return render_template("sms_settings.html", settings=current_settings, sms_status=sms_status)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
