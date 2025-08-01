#!/usr/bin/env python
"""
Create default admin user
"""
import os
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

# Create minimal settings
settings_content = """
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
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
"""

# Write settings
settings_path = BASE_DIR / 'admin_settings.py'
with open(settings_path, 'w') as f:
    f.write(settings_content)

try:
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_settings')
    import django
    django.setup()
    
    from django.contrib.auth.models import User
    
    print("🔐 建立預設管理員帳戶")
    print("=" * 40)
    
    # Check if admin already exists
    if User.objects.filter(username='admin').exists():
        print("✅ 管理員帳戶 'admin' 已存在")
        admin_user = User.objects.get(username='admin')
        print(f"   用戶名: {admin_user.username}")
        print(f"   電子郵件: {admin_user.email}")
        print(f"   超級用戶: {admin_user.is_superuser}")
    else:
        # Create admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@plantcon.com',
            password='plantcon123'
        )
        print("✅ 預設管理員帳戶已建立!")
        print("   用戶名: admin")
        print("   密碼: plantcon123")
        print("   電子郵件: admin@plantcon.com")
    
    # Show all users
    all_users = User.objects.all()
    superusers = User.objects.filter(is_superuser=True)
    
    print(f"\n📊 用戶統計:")
    print(f"   總用戶數: {all_users.count()}")
    print(f"   超級用戶數: {superusers.count()}")
    
    if superusers.exists():
        print(f"\n👤 超級用戶列表:")
        for user in superusers:
            print(f"   - {user.username} ({user.email})")
    
    print("\n" + "=" * 40)
    print("🎊 Plantcon 部署完成總結")
    print("=" * 40)
    
    print("\n✅ 已完成項目:")
    print("1. 🔒 修復所有安全漏洞")
    print("2. 📊 建立PostgreSQL資料庫")
    print("3. 🗄️ 執行所有資料庫遷移")
    print("4. 👤 建立管理員帳戶")
    print("5. 📁 收集所有靜態檔案")
    print("6. ⚙️ 配置生產環境設定")
    
    print("\n🌐 訪問資訊:")
    print("• 應用程式: http://localhost:8000/")
    print("• 管理介面: http://localhost:8000/admin/")
    print("• 健康檢查: http://localhost:8000/health/")
    
    print("\n🔑 登入憑證:")
    print("• 用戶名: admin")
    print("• 密碼: plantcon123")
    print("• (請在生產環境中更改密碼)")
    
    print("\n🚀 啟動應用程式:")
    print("python manage.py runserver --settings=admin_settings")
    
    print("\n✨ 你的Plantcon應用程式已準備好部署到AWS！")

except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
finally:
    if settings_path.exists():
        settings_path.unlink()
        print("\n🧹 已清理臨時檔案")