#!/usr/bin/env python
"""
Test database connection script
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Load environment variables
load_dotenv(BASE_DIR / '.env')

print("Environment variables loaded:")
print(f"DJANGO_ENVIRONMENT: {os.getenv('DJANGO_ENVIRONMENT')}")
print(f"RDS_HOSTNAME: {os.getenv('RDS_HOSTNAME')}")
print(f"RDS_DB_NAME: {os.getenv('RDS_DB_NAME')}")

# Test direct PostgreSQL connection
try:
    import psycopg2
    
    conn = psycopg2.connect(
        host=os.getenv('RDS_HOSTNAME'),
        database=os.getenv('RDS_DB_NAME'),
        user=os.getenv('RDS_USERNAME'),
        password=os.getenv('RDS_PASSWORD'),
        port=os.getenv('RDS_PORT', 5432)
    )
    
    cur = conn.cursor()
    cur.execute('SELECT version()')
    version = cur.fetchone()
    print(f"✅ Direct PostgreSQL connection successful!")
    print(f"PostgreSQL version: {version[0][:50]}...")
    
    # Check if tables exist
    cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
    table_count = cur.fetchone()[0]
    print(f"Number of tables: {table_count}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Direct PostgreSQL connection failed: {e}")
    sys.exit(1)

# Now test Django settings
print("\nTesting Django settings...")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plantcon.settings')

try:
    import django
    django.setup()
    
    from django.conf import settings
    from django.db import connection
    
    print(f"Django DEBUG: {settings.DEBUG}")
    print(f"Django DATABASES: {settings.DATABASES}")
    
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print("✅ Django database connection successful!")
        
except Exception as e:
    print(f"❌ Django database connection failed: {e}")
    import traceback
    traceback.print_exc()