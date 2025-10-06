# PricePick Backend Setup Guide

This guide will help you set up the PricePick backend with MySQL database and SMTP email configuration.

## Prerequisites

- Python 3.8+
- MySQL database server
- SMTP email service (Gmail, Outlook, etc.)

## Environment Configuration

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Edit the `.env` file with your configuration:

### Database Configuration
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=pricepick
```

### SMTP Email Configuration
```env
# Email Notification Settings
ENABLE_EMAIL_NOTIFICATIONS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
```

### Other Required Settings
```env
SECRET_KEY=your-secret-key-change-in-production
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
FIREBASE_DATABASE_URL=https://your-app.firebaseio.com
FIREBASE_STORAGE_BUCKET=your-app.appspot.com
```

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Database Setup

1. Make sure MySQL is running
2. Create the database:
   ```sql
   CREATE DATABASE pricepick;
   ```

3. Run the database setup script:
   ```bash
   python setup_database.py
   ```

This will:
- Test the database connection
- Create all necessary tables
- Create performance indexes
- Verify the setup

## SMTP Setup

### Gmail Setup
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
3. Use the App Password in your `.env` file

### Other SMTP Providers
- **Outlook/Hotmail**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom SMTP**: Use your provider's settings

## Running the Application

1. Start the development server:
   ```bash
   python main.py
   ```

2. The API will be available at `http://localhost:8000`

## Testing the Setup

1. Check the database connection:
   ```bash
   python -c "from app.database.init import test_connection; print('Database OK' if test_connection() else 'Database Error')"
   ```

2. Test email configuration:
   ```bash
   python -c "from config import settings; print('SMTP configured' if all([settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]) else 'SMTP configuration incomplete')"
   ```

## Troubleshooting

### Database Connection Issues
- Verify your MySQL server is running
- Check that the database exists: `CREATE DATABASE pricepick;`
- Verify user permissions
- Check firewall settings

### Email Issues
- For Gmail: Use App Password, not your regular password
- Check SMTP settings with your email provider
- Ensure `ENABLE_EMAIL_NOTIFICATIONS=true` in your `.env` file
- Test with a simple email first

### Import Errors
- Make sure you're in the backend directory
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check that your virtual environment is activated

## Configuration Examples

### Complete .env Example
```env
# Application Settings
APP_NAME=PricePick
VERSION=1.0.0
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-super-secret-key-here
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-app.firebaseapp.com
FIREBASE_DATABASE_URL=https://your-app.firebaseio.com
FIREBASE_STORAGE_BUCKET=your-app.appspot.com

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Price Monitoring Settings
PRICE_CHECK_INTERVAL=3600
MAX_PRICE_HISTORY_DAYS=90
PRICE_CHANGE_THRESHOLD=0.05

# Web Scraping Settings
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=5
USER_AGENT=PricePick/1.0 (Price Tracking Bot)

# Email Notification Settings
ENABLE_EMAIL_NOTIFICATIONS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=pricepick

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Cache Settings
REDIS_URL=
CACHE_TTL=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=
```
