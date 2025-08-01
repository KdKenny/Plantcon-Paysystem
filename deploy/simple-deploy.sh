#!/bin/bash

# Simple AWS Deployment Script for Plantcon Django Application
# This script assumes AWS infrastructure already exists

set -e

# Configuration
APP_NAME="plantcon"
AWS_REGION="ap-southeast-2"
ECR_REPOSITORY="$APP_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
else
    log_error ".env file not found. Please create it first."
    exit 1
fi

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    log_info "Prerequisites checked."
}

# Test AWS connection with provided credentials
test_aws_connection() {
    log_info "Testing AWS connection..."
    
    export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
    export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
    export AWS_DEFAULT_REGION=$AWS_REGION
    
    # Try to get caller identity
    if aws sts get-caller-identity &> /dev/null; then
        log_info "AWS connection successful."
        return 0
    else
        log_warn "AWS credentials might be temporary tokens or expired."
        log_info "Please ensure you have valid AWS credentials configured."
        log_info "You can run: aws configure"
        return 1
    fi
}

# Create ECR repository if it doesn't exist
create_ecr_repository() {
    log_info "Checking ECR repository..."
    
    aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION &> /dev/null || {
        log_info "Creating ECR repository: $ECR_REPOSITORY"
        aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
    }
}

# Build Docker image locally
build_docker_image() {
    log_info "Building Docker image locally..."
    
    cd ..
    
    # Build the image
    docker build -t $ECR_REPOSITORY:latest .
    
    log_info "Docker image built successfully."
    
    cd deploy
}

# Test database connection
test_database_connection() {
    log_info "Testing database connection..."
    
    cd ..
    
    # Try to connect to database using Django
    python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'plantcon.settings')
django.setup()
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" || {
        log_error "Database connection failed. Please check your RDS configuration."
        cd deploy
        return 1
    }
    
    cd deploy
    log_info "Database connection successful."
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd ..
    
    python manage.py migrate || {
        log_error "Migration failed."
        cd deploy
        return 1
    }
    
    log_info "Migrations completed successfully."
    cd deploy
}

# Collect static files
collect_static() {
    log_info "Collecting static files..."
    
    cd ..
    
    python manage.py collectstatic --noinput || {
        log_error "Static file collection failed."
        cd deploy
        return 1
    }
    
    log_info "Static files collected successfully."
    cd deploy
}

# Create superuser (optional)
create_superuser() {
    log_info "Creating superuser (optional)..."
    
    cd ..
    
    echo "You can create a superuser now or skip this step."
    read -p "Do you want to create a superuser? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python manage.py createsuperuser
    else
        log_info "Skipping superuser creation."
    fi
    
    cd deploy
}

# Test application locally
test_application() {
    log_info "Testing application locally..."
    
    cd ..
    
    log_info "Starting Django development server for testing..."
    log_info "Press Ctrl+C to stop the server and continue deployment."
    
    python manage.py runserver 0.0.0.0:8000 || {
        log_warn "Local testing interrupted or failed."
    }
    
    cd deploy
}

# Deploy to existing AWS infrastructure
deploy_to_aws() {
    log_info "Deploying to AWS..."
    
    if test_aws_connection; then
        create_ecr_repository
        
        # Get ECR login and push image
        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com
        
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"
        
        docker tag $ECR_REPOSITORY:latest $IMAGE_URI
        docker push $IMAGE_URI
        
        log_info "Image pushed to ECR: $IMAGE_URI"
        
        # Update ECS service if it exists
        if aws ecs describe-services --cluster plantcon-cluster --services plantcon-service --region $AWS_REGION &> /dev/null; then
            log_info "Updating ECS service..."
            aws ecs update-service --cluster plantcon-cluster --service plantcon-service --force-new-deployment --region $AWS_REGION
        else
            log_warn "ECS service not found. Please create it manually or use the full infrastructure deployment."
        fi
    else
        log_warn "Skipping AWS deployment due to credential issues."
        log_info "You can deploy manually using the Docker image: $ECR_REPOSITORY:latest"
    fi
}

# Main deployment function
main() {
    log_info "Starting simplified deployment of $APP_NAME..."
    
    check_prerequisites
    build_docker_image
    test_database_connection
    run_migrations
    collect_static
    create_superuser
    
    echo
    log_info "Local setup completed successfully!"
    echo
    
    read -p "Do you want to test the application locally first? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_application
    fi
    
    echo
    read -p "Do you want to deploy to AWS now? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        deploy_to_aws
    else
        log_info "Skipping AWS deployment."
    fi
    
    log_info "Deployment process completed!"
    log_info "If AWS deployment was successful, check your ECS service status."
}

# Run main function
main "$@"