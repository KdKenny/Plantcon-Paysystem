#!/usr/bin/env python
"""
Test the Django application
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import sys

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

# Create temporary settings for testing
temp_settings = f"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = os.getenv('SITE_SECRET_KEY')
DEBUG = True  # Enable debug for testing
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
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'plantcon/static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging for testing
LOGGING = {{
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {{
        'console': {{
            'class': 'logging.StreamHandler',
        }},
    }},
    'root': {{
        'handlers': ['console'],
        'level': 'INFO',
    }},
}}
"""

# Write temporary settings
temp_settings_path = BASE_DIR / 'test_settings.py'
with open(temp_settings_path, 'w') as f:
    f.write(temp_settings)

try:
    print("🧪 Testing Django application...")
    print("=" * 50)
    
    # Test basic Django functionality
    print("1. Testing Django check...")
    result = subprocess.run([
        sys.executable, 'manage.py', 'check', '--settings=test_settings'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Django check passed")
    else:
        print(f"❌ Django check failed: {result.stderr}")
    
    # Test health endpoint
    print("\n2. Testing health endpoint...")
    result = subprocess.run([
        sys.executable, '-c', 
        """
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')
import django
django.setup()
from django.test import Client
client = Client()
response = client.get('/health/')
print(f'Health endpoint status: {response.status_code}')
if response.status_code == 200:
    import json
    data = json.loads(response.content)
    print(f'Health status: {data.get("status")}')
    print(f'Database: {data.get("database")}')
else:
    print(f'Response: {response.content.decode()}')
"""
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Health endpoint test:")
        print(result.stdout)
    else:
        print(f"❌ Health endpoint test failed: {result.stderr}")
    
    print("\n3. Starting development server for testing...")
    print("🌐 Server will start on http://localhost:8000")
    print("📋 You can access:")
    print("   - Login page: http://localhost:8000/")
    print("   - Admin panel: http://localhost:8000/admin/")
    print("   - Health check: http://localhost:8000/health/")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the development server
    subprocess.run([
        sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000', '--settings=test_settings'
    ])

except KeyboardInterrupt:
    print("\n✅ Server stopped by user")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    # Clean up
    if temp_settings_path.exists():
        temp_settings_path.unlink()
        print("🧹 Cleaned up temporary files")