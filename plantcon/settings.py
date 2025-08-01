"""
Django settings for plantcon project.

This file imports the appropriate settings based on the DJANGO_ENVIRONMENT environment variable.
For production, set DJANGO_ENVIRONMENT=production
For development, use DJANGO_ENVIRONMENT=development (default)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Determine which settings to use
environment = os.getenv('DJANGO_ENVIRONMENT', 'development')

if environment == 'production':
    from .settings.production import *
elif environment == 'development':
    from .settings.development import *
else:
    # Default to development settings
    from .settings.development import *