#!/usr/bin/env python
"""
Start Plantcon locally for testing
"""
import os
import subprocess
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

# Create minimal settings for local testing
settings_content = """
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.getenv('SITE_SECRET_KEY')
DEBUG = True  # Enable for local testing
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
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'plantcon.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('RDS_DB_NAME'),
        'USER': os.getenv('RDS_USERNAME'),
        'PASSWORD': os.getenv('RDS_PASSWORD'),
        'HOST': os.getenv('RDS_HOSTNAME'),
        'PORT': os.getenv('RDS_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Hong_Kong'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'plantcon/static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Enable detailed logging for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
"""

# Write local settings
settings_path = BASE_DIR / 'local_settings.py'
with open(settings_path, 'w') as f:
    f.write(settings_content)

try:
    print("🚀 啟動Plantcon本地服務器")
    print("=" * 50)
    
    print("📊 環境檢查:")
    print(f"✅ 資料庫: {os.getenv('RDS_HOSTNAME', 'Unknown')}")
    print(f"✅ 區域: {os.getenv('AWS_REGION', 'Unknown')}")
    print(f"✅ 用戶: admin / plantcon123")
    
    print("\n🌐 訪問資訊:")
    print("• 主頁面: http://localhost:8000/")
    print("• 管理介面: http://localhost:8000/admin/")  
    print("• 健康檢查: http://localhost:8000/health/")
    
    print("\n🔑 登入憑證:")
    print("• 用戶名: admin")
    print("• 密碼: plantcon123")
    
    print("\n⚠️ 按 Ctrl+C 停止服務器")
    print("=" * 50)
    
    # Start Django development server
    subprocess.run([
        sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000', '--settings=local_settings'
    ])

except KeyboardInterrupt:
    print("\n✅ 服務器已停止")
except Exception as e:
    print(f"❌ 錯誤: {e}")
finally:
    if settings_path.exists():
        settings_path.unlink()
        print("🧹 已清理臨時檔案")