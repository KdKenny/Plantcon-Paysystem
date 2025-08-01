#!/usr/bin/env python
"""
Create Django superuser with temporary settings
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

# Set environment variables
env_vars = {
    'DJANGO_ENVIRONMENT': 'production',
    'SITE_SECRET_KEY': os.getenv('SITE_SECRET_KEY'),
    'RDS_DB_NAME': os.getenv('RDS_DB_NAME'),
    'RDS_USERNAME': os.getenv('RDS_USERNAME'),
    'RDS_PASSWORD': os.getenv('RDS_PASSWORD'),
    'RDS_HOSTNAME': os.getenv('RDS_HOSTNAME'),
    'RDS_PORT': os.getenv('RDS_PORT', '5432'),
    'AWS_REGION': os.getenv('AWS_REGION'),
}

for key, value in env_vars.items():
    if value:
        os.environ[key] = str(value)

# Create temporary settings
temp_settings = f"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.getenv('SITE_SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'pages.apps.PagesConfig',
    'addinvoice.apps.AddinvoiceConfig',
    'processpay.apps.ProcesspayConfig',
    'statement.apps.StatementConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'plantcon.urls'

TEMPLATES = [
    {{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {{
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        }},
    }},
]

WSGI_APPLICATION = 'plantcon.wsgi.application'

DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('RDS_DB_NAME'),
        'USER': os.getenv('RDS_USERNAME'),
        'PASSWORD': os.getenv('RDS_PASSWORD'),
        'HOST': os.getenv('RDS_HOSTNAME'),
        'PORT': os.getenv('RDS_PORT', '5432'),
        'OPTIONS': {{
            'sslmode': 'require',
        }},
    }}
}}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Hong_Kong'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
"""

# Write temporary settings file
temp_settings_path = BASE_DIR / 'temp_settings.py'
with open(temp_settings_path, 'w') as f:
    f.write(temp_settings)

try:
    print("Creating Django superuser...")
    print("Please follow the prompts to create an admin user for your application.")
    
    import subprocess
    result = subprocess.run([
        sys.executable, 'manage.py', 'createsuperuser', '--settings=temp_settings'
    ], check=True)
    
    print("✅ Superuser created successfully!")
    
finally:
    # Clean up
    if temp_settings_path.exists():
        temp_settings_path.unlink()
        print("🧹 Cleaned up temporary files")