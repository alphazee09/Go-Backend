# Go4Rent Dashboard Production Deployment Guide

This guide provides instructions for deploying the Go4Rent Dashboard application to a production environment.

## Prerequisites

- Ubuntu 20.04 LTS or newer
- PostgreSQL 12 or newer
- Python 3.10 or newer
- Node.js 16 or newer
- Nginx
- Certbot (for SSL)

## Backend Deployment

### 1. Set Up the Server

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx certbot python3-certbot-nginx
```

### 2. Create a PostgreSQL Database

```bash
# Create database user
sudo -u postgres createuser --interactive
# Enter name of role to add: go4rent
# Shall the new role be a superuser? (y/n): n
# Shall the new role be allowed to create databases? (y/n): n
# Shall the new role be allowed to create more new roles? (y/n): n

# Create database and set password
sudo -u postgres psql
postgres=# CREATE DATABASE go4rent;
postgres=# ALTER USER go4rent WITH ENCRYPTED PASSWORD 'secure_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE go4rent TO go4rent;
postgres=# \q

# Import database schema
sudo -u postgres psql go4rent < /path/to/database.sql
```

### 3. Set Up the Django Application

```bash
# Create directory for the application
sudo mkdir -p /var/www/go4rent
sudo chown -R $USER:$USER /var/www/go4rent

# Clone the repository or copy the files
# git clone https://your-repository.git /var/www/go4rent
# OR
# cp -r /path/to/go4rent_backend/* /var/www/go4rent/

# Create and activate virtual environment
cd /var/www/go4rent
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Create production settings
cp go4rent/settings.py go4rent/settings_prod.py
```

### 4. Configure Production Settings

Edit `/var/www/go4rent/go4rent/settings_prod.py`:

```python
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your-secure-secret-key'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'go4rent',
        'USER': 'go4rent',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### 5. Set Up Gunicorn Service

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/go4rent.service
```

Add the following content:

```
[Unit]
Description=Go4Rent Dashboard Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/go4rent
ExecStart=/var/www/go4rent/venv/bin/gunicorn --workers 3 --bind unix:/var/www/go4rent/go4rent.sock go4rent.wsgi:application --env DJANGO_SETTINGS_MODULE=go4rent.settings_prod
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Start and enable the service:

```bash
sudo systemctl start go4rent
sudo systemctl enable go4rent
```

### 6. Configure Nginx

Create an Nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/go4rent
```

Add the following content:

```
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/go4rent;
    }

    location /media/ {
        root /var/www/go4rent;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/go4rent/go4rent.sock;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/go4rent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Set Up SSL with Certbot

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 8. Collect Static Files

```bash
cd /var/www/go4rent
source venv/bin/activate
python manage.py collectstatic --settings=go4rent.settings_prod
```

### 9. Set Proper Permissions

```bash
sudo chown -R www-data:www-data /var/www/go4rent
sudo chmod -R 755 /var/www/go4rent
```

## Frontend Deployment

### 1. Build the Frontend

```bash
# Navigate to the frontend directory
cd /path/to/go4rent

# Install dependencies
npm install

# Update API configuration
# Edit /path/to/go4rent/lib/api-config.ts to point to your production API

# Build the application
npm run build
```

### 2. Configure Nginx for Frontend

Edit the Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/go4rent
```

Update to include frontend serving:

```
server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Frontend static files
    location / {
        root /var/www/go4rent-frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        include proxy_params;
        proxy_pass http://unix:/var/www/go4rent/go4rent.sock;
    }
    
    location /admin/ {
        include proxy_params;
        proxy_pass http://unix:/var/www/go4rent/go4rent.sock;
    }
    
    location /static/admin/ {
        alias /var/www/go4rent/static/admin/;
    }
    
    location /static/ {
        root /var/www/go4rent;
    }
    
    location /media/ {
        root /var/www/go4rent;
    }
}
```

### 3. Deploy Frontend Files

```bash
# Create directory for frontend
sudo mkdir -p /var/www/go4rent-frontend
sudo chown -R $USER:$USER /var/www/go4rent-frontend

# Copy built files
cp -r /path/to/go4rent/dist/* /var/www/go4rent-frontend/dist/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/go4rent-frontend
sudo chmod -R 755 /var/www/go4rent-frontend

# Restart Nginx
sudo systemctl restart nginx
```

## Maintenance and Monitoring

### 1. Set Up Database Backups

Create a backup script:

```bash
sudo nano /usr/local/bin/backup-go4rent-db.sh
```

Add the following content:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/go4rent"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/go4rent_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create backup
sudo -u postgres pg_dump go4rent > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +30 -delete
```

Make the script executable:

```bash
sudo chmod +x /usr/local/bin/backup-go4rent-db.sh
```

Set up a cron job:

```bash
sudo crontab -e
```

Add the following line:

```
0 2 * * * /usr/local/bin/backup-go4rent-db.sh
```

### 2. Set Up Log Rotation

Create a log rotation configuration:

```bash
sudo nano /etc/logrotate.d/go4rent
```

Add the following content:

```
/var/www/go4rent/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload go4rent.service
    endscript
}
```

### 3. Monitoring

Consider setting up monitoring with tools like:

- Prometheus and Grafana for metrics
- Sentry for error tracking
- Uptime Robot for availability monitoring

## Updating the Application

### Backend Updates

```bash
# Navigate to the backend directory
cd /var/www/go4rent

# Activate virtual environment
source venv/bin/activate

# Pull latest changes (if using git)
git pull

# Install any new dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate --settings=go4rent.settings_prod

# Collect static files
python manage.py collectstatic --settings=go4rent.settings_prod

# Restart the service
sudo systemctl restart go4rent
```

### Frontend Updates

```bash
# Build the updated frontend locally
cd /path/to/go4rent
npm install
npm run build

# Deploy the updated files
cp -r /path/to/go4rent/dist/* /var/www/go4rent-frontend/dist/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/go4rent-frontend
```

## Troubleshooting

### Check Backend Service Status

```bash
sudo systemctl status go4rent
```

### View Backend Logs

```bash
sudo journalctl -u go4rent
```

### Check Nginx Status

```bash
sudo systemctl status nginx
```

### View Nginx Logs

```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Check Database Connection

```bash
cd /var/www/go4rent
source venv/bin/activate
python manage.py shell --settings=go4rent.settings_prod
```

Then in the Python shell:

```python
from django.db import connections
connections['default'].ensure_connection()
```

## Security Considerations

1. Regularly update all system packages
2. Use strong, unique passwords for all services
3. Implement IP-based access restrictions for admin areas
4. Set up a firewall (UFW)
5. Configure fail2ban to prevent brute force attacks
6. Regularly review logs for suspicious activity
7. Keep backups in a separate location
8. Implement HTTPS with strong SSL configuration
9. Use secure headers in Nginx configuration
10. Regularly rotate API keys and secrets

## Conclusion

This deployment guide provides a comprehensive approach to deploying the Go4Rent Dashboard application in a production environment. Following these steps will result in a secure, maintainable, and scalable deployment.
