#!/usr/bin/env python
"""
Direct deployment script for Plantcon to AWS
Bypasses Django settings issues and works with existing infrastructure
"""
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

def run_command(cmd, description):
    """Run a shell command and return the result"""
    print(f"\n🔄 {description}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Starting Plantcon AWS Deployment")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ['AWS_REGION', 'RDS_HOSTNAME', 'RDS_DB_NAME', 'RDS_USERNAME', 'RDS_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {os.getenv(var)[:20]}...")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    # Step 1: Run migrations directly with environment variables
    print("\n📊 Step 1: Running Database Migrations")
    
    env_vars = {
        'DJANGO_ENVIRONMENT': 'production',
        'SITE_SECRET_KEY': os.getenv('SITE_SECRET_KEY'),
        'RDS_DB_NAME': os.getenv('RDS_DB_NAME'),
        'RDS_USERNAME': os.getenv('RDS_USERNAME'),
        'RDS_PASSWORD': os.getenv('RDS_PASSWORD'),
        'RDS_HOSTNAME': os.getenv('RDS_HOSTNAME'),
        'RDS_PORT': os.getenv('RDS_PORT', '5432'),
        'AWS_REGION': os.getenv('AWS_REGION'),
        'USE_S3': 'FALSE',  # Disable S3 for now
    }
    
    # Create a temporary settings file for migration
    temp_settings = f"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Set environment variables
for key, value in {env_vars}.items():
    if value:
        os.environ[key] = str(value)

SECRET_KEY = os.getenv('SITE_SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = ['*']  # Temporary for migration

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

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'plantcon/static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Minimal logging
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
    }},
}}
"""
    
    # Write temporary settings file
    temp_settings_path = BASE_DIR / 'temp_settings.py'
    with open(temp_settings_path, 'w') as f:
        f.write(temp_settings)
    
    try:
        # Run migrations with temporary settings
        migrate_cmd = f"python manage.py migrate --settings=temp_settings"
        if run_command(migrate_cmd, "Database Migration"):
            print("✅ Database migration completed successfully!")
        else:
            print("❌ Database migration failed!")
            return False
        
        # Collect static files
        collectstatic_cmd = f"python manage.py collectstatic --noinput --settings=temp_settings"
        if run_command(collectstatic_cmd, "Collect Static Files"):
            print("✅ Static files collected successfully!")
        else:
            print("❌ Static file collection failed!")
        
        # Create superuser (optional)
        print("\n👤 Create Superuser")
        create_superuser = input("Do you want to create a superuser? (y/n): ").lower().strip() == 'y'
        
        if create_superuser:
            superuser_cmd = f"python manage.py createsuperuser --settings=temp_settings"
            subprocess.run(superuser_cmd, shell=True)
        
        # Step 2: Build Docker image
        print("\n🐳 Step 2: Building Docker Image")
        if run_command("docker build -t plantcon:latest .", "Build Docker Image"):
            print("✅ Docker image built successfully!")
        else:
            print("❌ Docker image build failed!")
            return False
        
        # Step 3: Test locally (optional)
        print("\n🧪 Step 3: Local Testing")
        test_locally = input("Do you want to test the application locally first? (y/n): ").lower().strip() == 'y'
        
        if test_locally:
            print("Starting local test server...")
            print("Press Ctrl+C to stop and continue with deployment")
            try:
                subprocess.run([
                    "docker", "run", "-p", "8000:8000",
                    "-e", f"DJANGO_ENVIRONMENT=production",
                    "-e", f"SITE_SECRET_KEY={os.getenv('SITE_SECRET_KEY')}",
                    "-e", f"RDS_DB_NAME={os.getenv('RDS_DB_NAME')}",
                    "-e", f"RDS_USERNAME={os.getenv('RDS_USERNAME')}",
                    "-e", f"RDS_PASSWORD={os.getenv('RDS_PASSWORD')}",
                    "-e", f"RDS_HOSTNAME={os.getenv('RDS_HOSTNAME')}",
                    "-e", f"RDS_PORT={os.getenv('RDS_PORT', '5432')}",
                    "-e", f"AWS_REGION={os.getenv('AWS_REGION')}",
                    "plantcon:latest"
                ])
            except KeyboardInterrupt:
                print("\n✅ Local test stopped by user")
        
        print("\n🎉 Deployment preparation completed successfully!")
        print("\nNext steps:")
        print("1. Your database is ready with migrations applied")
        print("2. Docker image 'plantcon:latest' is built")
        print("3. Push to ECR and update ECS service if needed")
        print("\nTo push to ECR and deploy:")
        print("cd deploy && chmod +x simple-deploy.sh && ./simple-deploy.sh")
        
        return True
        
    finally:
        # Clean up temporary settings file
        if temp_settings_path.exists():
            temp_settings_path.unlink()
            print("🧹 Cleaned up temporary files")

if __name__ == "__main__":
    if main():
        print("\n✅ All tasks completed successfully!")
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)