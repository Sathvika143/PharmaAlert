# PharmaAlert: Automated Drug Expiry & Stock Notification System

##  Overview
PharmaAlert is an intelligent drug expiry and stock management system designed to help pharmacies efficiently track medicine inventory. It automates expiry date monitoring and sends timely notifications via **email** and **SMS** using **Twilio** and **SMTP**.

##  Features
- **Automated Drug Expiry Alerts**: Notifies users about medicines nearing expiry (within 6 months).
- **Stock Monitoring**: Helps manage medicine stock to prevent shortages.
- **Email & SMS Notifications**: Sends alerts via **Gmail SMTP** and **Twilio SMS**.
- **Database Integration**: Uses SQLite to store and retrieve medicine stock data.
- **User-Friendly Execution**: Simple and automated process for pharmacies.

##  Tech Stack
- **Programming Language**: Python
- **Database**: SQLite
- **Deploy**: Flask API
- **Messaging Services**: Twilio (SMS) & Gmail SMTP (Email)
- **Environment Variables**: `.env` file for storing credentials securely


## Project Structure
```
├── static/
│   ├── style.css
├── templates/
│   ├── alerts.html
│   ├── index.html
├── venv/                   # Virtual environment (not included in Git)
├── .env                    # Environment variables (ignored in Git)
├── .gitignore
├── app.py                  # Flask web application
├── database.py             # Database initialization script
├── expiry_checker.py       # Checks expiry dates and triggers notifications
├── medicine_data.csv       # Sample medicine data
├── notifier.py             # Handles email and SMS notifications
├── pharmacy.db             # SQLite database
├── README.md               # Project documentation
├── requirements.txt        # Dependencies
```

##  Setup & Installation
### 1️⃣ Clone the Repository
```sh
git clone https://github.com/mansisawantt/Drug-Expiry-Stock-Management-System.git
cd Drug-Expiry-Stock-Management-System
```
### 2️⃣ Create a Virtual Environment
```sh
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows
```
### 3️⃣ Install Dependencies
```sh
pip install -r requirements.txt
```
### 4️⃣ Configure Environment Variables
Create a `.env` file in the project root and add the following:
```env
# Email Credentials
EMAIL_SENDER="your_email@gmail.com"
EMAIL_PASSWORD="your_app_password"
EMAIL_RECEIVER="receiver_email@gmail.com"

# Twilio Credentials
TWILIO_SID="your_twilio_sid"
TWILIO_AUTH_TOKEN="your_twilio_auth_token"
TWILIO_PHONE_NUMBER="+1234567890"
RECEIVER_PHONE_NUMBER="+919876543210"
```
> **Note**: Use an **App Password** for Gmail authentication. [Generate an App Password](https://support.google.com/accounts/answer/185833?hl=en).

### 5️⃣ Run the Notifier Script
```sh
python notifier.py
```

## 📧 How Notifications Work
- The script fetches **medicine stock** from `pharmacy.db`.
- It checks for medicines expiring **within the next 6 months**.
- If any are found, it **sends alerts** via **email** and **SMS**.
- If no expiring medicines are found, it displays: `No medicines expiring soon.`


