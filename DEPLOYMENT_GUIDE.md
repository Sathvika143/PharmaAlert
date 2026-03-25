# 🚀 PharmaAlert Deployment Guide

Complete step-by-step deployment instructions for all platforms.

---

## 📋 Pre-Deployment Checklist

- [ ] Update `.env` file with production settings
- [ ] Change default login credentials (admin/admin123)
- [ ] Back up your `pharmacy.db` database
- [ ] Ensure `requirements.txt` has all packages
- [ ] Test app locally one more time

---

## 🔐 Production Environment Setup

### Update `.env` for Production:

```env
# Production Settings
FLASK_ENV=production
DEBUG=False

# Email Configuration
EMAIL_SENDER="puppypanuganti06@gmail.com"
EMAIL_PASSWORD="qxxo wrbm rebt ktku"
EMAIL_RECEIVER="puppypanuganti06@gmail.com"

# Alert Configuration
EXPIRY_LEAD_DAYS=180

# SMS (optional)
TWILIO_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN="your_auth_token_here"
TWILIO_PHONE_NUMBER="+1234567890"
RECEIVER_PHONE_NUMBER="+919876543210"
```

---

## 🌐 Deployment Option 1: RENDER (⭐ Recommended - Easiest)

### Step 1: Push to GitHub

```powershell
# Initialize git if not done
git init
git config user.email "your-email@example.com"
git config user.name "Your Name"

# Add and commit all files
git add .
git commit -m "PharmaAlert v1.0 - Ready for deployment"

# Create repository on GitHub.com manually first, then:
git remote add origin https://github.com/YOUR-USERNAME/PharmaAlert.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to **https://render.com** (free account)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account
4. Select **PharmaAlert** repository
5. Fill deployment settings:
   - **Name:** PharmaAlert
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
6. Click **"Advanced"** and add Environment Variables:
   ```
   EMAIL_SENDER = puppypanuganti06@gmail.com
   EMAIL_PASSWORD = qxxo wrbm rebt ktku
   EMAIL_RECEIVER = puppypanuganti06@gmail.com
   EXPIRY_LEAD_DAYS = 180
   FLASK_ENV = production
   DEBUG = False
   ```
7. Click **"Deploy"** → Done! (5-10 minutes)
8. Your app will be at: **https://YourAppName.onrender.com**

✅ **Pros:** Free, auto-restarts, easy to update
⚠️ **Note:** Free tier sleeps after 15 min inactivity (upgrade to prevent)

---

## 🎯 Deployment Option 2: HEROKU

### Step 1: Install Heroku CLI

```powershell
# Download from https://devcenter.heroku.com/articles/heroku-cli
# Verify installation
heroku --version
```

### Step 2: Deploy

```powershell
# Login to Heroku
heroku login

# Create app
heroku create your-pharmalert-app

# Set environment variables
heroku config:set EMAIL_SENDER="puppypanuganti06@gmail.com"
heroku config:set EMAIL_PASSWORD="qxxo wrbm rebt ktku"
heroku config:set EMAIL_RECEIVER="puppypanuganti06@gmail.com"
heroku config:set EXPIRY_LEAD_DAYS="180"
heroku config:set FLASK_ENV="production"
heroku config:set DEBUG="False"

# Deploy from Git
git push heroku main

# View logs
heroku logs --tail
```

✅ **Pros:** Very reliable, good documentation
⚠️ **Note:** Free tier deprecated (requires paid plan)

---

## 🐍 Deployment Option 3: PYTHONANYWHERE

### Step 1: Sign Up

1. Go to **https://www.pythonanywhere.com**
2. Create free account (no credit card needed)
3. Confirm email

### Step 2: Upload Files

1. Go to **"Files"** tab
2. Upload your project:
   - pharmacy.db
   - app.py
   - All Python files (operations.py, notifier.py, etc.)
   - templates/ folder
   - static/ folder
   - requirements.txt

### Step 3: Create Web App

1. Click **"Web"** tab
2. **"Add new web app"**
3. Select **"Python 3.11"**
4. Select **"Flask"**
5. Create WSGI file at `/var/www/username_pythonanywhere_com_wsgi.py`:

```python
import sys
path = '/home/username/PharmaAlert'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

### Step 4: Install Packages

Go to **"Consoles"** → **"Bash"**:

```bash
pip install -r /home/username/PharmaAlert/requirements.txt
```

### Step 5: Set Environment Variables

In web app settings, add to **"Environment variables"**:

```
EMAIL_SENDER=puppypanuganti06@gmail.com
EMAIL_PASSWORD=qxxo wrbm rebt ktku
EMAIL_RECEIVER=puppypanuganti06@gmail.com
EXPIRY_LEAD_DAYS=180
FLASK_ENV=production
DEBUG=False
```

✅ **Pros:** Python-specific, simple setup, free tier available
⚠️ **Note:** Limited to 100 requests/day on free tier

---

## ☁️ Deployment Option 4: AWS / Google Cloud / Azure

### AWS Elastic Beanstalk (Most Professional)

```powershell
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 pharmalert

# Create environment
eb create pharmalert-env

# Deploy
eb deploy

# View logs
eb logs
```

✅ **Pros:** Production-grade, highly scalable
⚠️ **Cost:** ~$5-50/month (free tier available)

---

## 📊 Database Backup (Cloud Deployment)

### Option 1: SQLite to PostgreSQL (Recommended)

```python
# Convert to PostgreSQL for cloud
pip install psycopg2-binary
# Use migration script to transfer data
```

### Option 2: Download & Backup

```powershell
# Backup locally before deploying
Copy-Item pharmacy.db pharmacy.db.backup
```

---

## 🧪 Test Your Deployment

After deployment:

1. Open your live URL: `https://your-app-name.onrender.com`
2. Login: `admin` / `admin123`
3. Go to Dashboard
4. Click **"🔔 Trigger Check Now"**
5. Check email for alert
6. Try adding a medicine via web interface
7. Verify all CRUD operations work

---

## 🔧 Troubleshooting

### ❌ "Application Error" on Heroku/Render

```powershell
# Check logs
heroku logs --tail
# or view in Render dashboard
```

### ❌ "Module not found"

```
Update requirements.txt with all imports
Redeploy
```

### ❌ "Email not sending"

- Verify `.env` variables in cloud dashboard
- Check spam folder
- Ensure app password is correct (not regular password)

### ❌ "Database error"

- Free tier databases have size limits
- Consider upgrading to PostgreSQL

---

## 📈 Next Steps

### After Successful Deployment:

1. **Change admin password:**
   - Login to app
   - Go to Settings (if available)
   - Create new users with strong passwords

2. **Set up custom domain:**
   - Buy domain from GoDaddy/Namecheap
   - Point to your cloud app

3. **Enable HTTPS:**
   - Auto-enabled on Render/Heroku
   - Recommended for production

4. **Monitor & Scale:**
   - Check logs daily
   - Upgrade if needed
   - Add more team members

---

## 📞 Support & Help

**For Render issues:** https://render.com/docs
**For Heroku issues:** https://devcenter.heroku.com
**For PythonAnywhere:** https://www.pythonanywhere.com/help
**For AWS:** https://aws.amazon.com/premiumsupport

---

**Recommended:** Start with **Render** (easiest) or **PythonAnywhere** (if free tier preferred).

Deploy now and your hospital can access PharmaAlert from anywhere! 🏥✨
