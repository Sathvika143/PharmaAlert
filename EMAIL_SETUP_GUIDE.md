# Email Notification Setup Guide

## What I've Added

✅ **Settings Page**: You can now configure email notifications through the web interface
✅ **Email Configuration**: Integrated Gmail SMTP for sending alerts
✅ **Test Email Feature**: Send a test email to verify your settings
✅ **Navigation Updates**: Added Settings link to all pages

## How to Set Up Email Notifications

### Step 1: Get Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Sign in to your Google Account
3. Select "Mail" as the app
4. Select "Windows Computer" as the device
5. Click "Generate"
6. Copy the 16-character password (it will look like: `xxxx xxxx xxxx xxxx`)

### Step 2: Configure Email in PharmaAlert

1. Start your PharmaAlert application
2. Login with your credentials (default: admin/admin123)
3. Click on **"Settings"** in the navigation menu
4. Fill in the form:
   - **Your Email Address**: Your Gmail address (e.g., sathvikakarumuri@gmail.com)
   - **Gmail App Password**: The 16-character password from Step 1
   - **Notification Recipient Email**: Where you want to receive alerts (can be the same email)
   - **Alert Days Before Expiry**: How many days in advance to alert (default: 180 = 6 months)
5. Click **"Save Settings"**
6. Click **"Send Test Email"** to verify it works

### Step 3: Verify Email Notifications

After saving your settings:
- Click the **"Send Test Email"** button
- Check your inbox (and spam folder if needed)
- You should receive a test email from PharmaAlert

## What Notifications You'll Receive

PharmaAlert automatically checks for alerts **every day at 9:00 AM** and sends emails if:

- 🔴 **Expired Medicines**: Already expired (URGENT)
- 🔴 **Critical**: Expiring within 30 days
- 🟡 **Warning**: Expiring in 31-90 days
- 🔵 **Notice**: Expiring in 91+ days
- 📉 **Low Stock**: Medicines below threshold

## Manual Check

You can also trigger a manual check anytime:
1. Go to Dashboard
2. Click **"🔔 Trigger Check Now"** button
3. Alerts will be sent immediately if any issues are found

## Current Configuration

Your `.env` file already has:
- Email Sender: `sathvikakarumuri@gmail.com`
- Email Receiver: `sathvikakarumuri@gmail.com`
- **You just need to add your Gmail App Password!**

## Troubleshooting

### Email Not Sending?
1. Make sure you're using an **App Password**, not your regular Gmail password
2. Check that "Less secure app access" is not required (App Passwords bypass this)
3. Verify your email address is correct
4. Check spam folder

### Still Not Working?
- Restart the application after saving settings
- Check the terminal/console for error messages
- Verify your Gmail account allows App Passwords

## Security Notes

- ⚠️ Never share your App Password
- ⚠️ Never commit your `.env` file to version control
- ⚠️ Use App Passwords instead of regular passwords for security
- ✅ Your `.env` file is already in `.gitignore` for safety

## Next Steps

1. Get your Gmail App Password
2. Add it in Settings page
3. Test the email
4. You're all set! 🎉

---

**Need Help?** Check the Settings page for detailed instructions on getting your Gmail App Password.
