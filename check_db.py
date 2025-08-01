#!/usr/bin/env python
"""
Check available databases on RDS instance
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

try:
    import psycopg2
    
    # Connect to default 'postgres' database to check what databases exist
    conn = psycopg2.connect(
        host=os.getenv('RDS_HOSTNAME'),
        database='postgres',  # Connect to default postgres database
        user=os.getenv('RDS_USERNAME'),
        password=os.getenv('RDS_PASSWORD'),
        port=os.getenv('RDS_PORT', 5432)
    )
    
    cur = conn.cursor()
    
    # List all databases
    cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
    databases = cur.fetchall()
    
    print("Available databases:")
    for db in databases:
        print(f"  - {db[0]}")
    
    cur.close()
    conn.close()
    
    # Try to create the plantcon database if it doesn't exist
    db_names = [db[0] for db in databases]
    if 'plantcon' not in db_names:
        print("\nCreating 'plantcon' database...")
        
        # Reconnect with autocommit for database creation
        conn = psycopg2.connect(
            host=os.getenv('RDS_HOSTNAME'),
            database='postgres',
            user=os.getenv('RDS_USERNAME'),
            password=os.getenv('RDS_PASSWORD'),
            port=os.getenv('RDS_PORT', 5432)
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("CREATE DATABASE plantcon;")
        cur.close()
        conn.close()
        print("✅ Database 'plantcon' created successfully!")
    else:
        print("\n✅ Database 'plantcon' already exists!")
    
except Exception as e:
    print(f"❌ Database check failed: {e}")
    import traceback
    traceback.print_exc()