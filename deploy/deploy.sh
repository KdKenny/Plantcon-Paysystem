#!/bin/bash

# AWS Deployment Script for Plantcon Django Application
# This script deploys the application to AWS using Docker and ECS

set -e

# Configuration
APP_NAME="plantcon"
AWS_REGION="us-east-1"
ECR_REPOSITORY="$APP_NAME"
ECS_CLUSTER="$APP_NAME-cluster"
ECS_SERVICE="$APP_NAME-service"

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
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    # if ! aws sts get-caller-identity &> /dev/null; then
    #     log_error "AWS credentials not configured. Please run 'aws configure'."
    #     exit 1
    # fi
    
    log_info "All prerequisites met."
}

# Create ECR repository if it doesn't exist
create_ecr_repository() {
    log_info "Creating ECR repository..."
    
    aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION &> /dev/null || {
        log_info "Creating ECR repository: $ECR_REPOSITORY"
        aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
    }
    
    # Get ECR login token
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com
}

# Build and push Docker image
build_and_push_image() {
    log_info "Building Docker image..."
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:latest"
    
    # Build the image
    docker build -f ../Dockerfile -t $ECR_REPOSITORY ..
    docker tag $ECR_REPOSITORY:latest $IMAGE_URI
    
    log_info "Pushing image to ECR..."
    docker push $IMAGE_URI
    
    echo $IMAGE_URI
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    
    # Initialize Terraform
    terraform init
    
    # Plan the deployment
    terraform plan -var="db_password=$DB_PASSWORD"
    
    # Apply the infrastructure
    terraform apply -var="db_password=$DB_PASSWORD" -auto-approve
    
    cd ..
}

# Create ECS task definition
create_task_definition() {
    local image_uri=$1
    log_info "Creating ECS task definition..."
    
    # Get infrastructure outputs
    cd deploy
    RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
    S3_BUCKET=$(terraform output -raw s3_bucket_name)
    ALB_DNS=$(terraform output -raw alb_dns_name)
    cd ..
    
    # Create task definition JSON
    cat > task-definition.json << EOF
{
  "family": "$APP_NAME-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "$APP_NAME-container",
      "image": "$image_uri",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DJANGO_ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "RDS_HOSTNAME",
          "value": "${RDS_ENDPOINT%:*}"
        },
        {
          "name": "RDS_DB_NAME",
          "value": "plantcon"
        },
        {
          "name": "RDS_USERNAME",
          "value": "plantcon_user"
        },
        {
          "name": "S3_BUCKET_NAME",
          "value": "$S3_BUCKET"
        },
        {
          "name": "AWS_REGION",
          "value": "$AWS_REGION"
        },
        {
          "name": "USE_S3",
          "value": "TRUE"
        },
        {
          "name": "ALB_DNS_NAME",
          "value": "$ALB_DNS"
        }
      ],
      "secrets": [
        {
          "name": "SITE_SECRET_KEY",
          "valueFrom": "arn:aws:ssm:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):parameter/plantcon/secret-key"
        },
        {
          "name": "RDS_PASSWORD",
          "valueFrom": "arn:aws:ssm:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):parameter/plantcon/db-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/$APP_NAME",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

    # Register task definition
    aws ecs register-task-definition \
        --cli-input-json file://task-definition.json \
        --region $AWS_REGION
    
    rm task-definition.json
}

# Create or update ECS service
deploy_service() {
    log_info "Deploying ECS service..."
    
    cd deploy
    VPC_ID=$(terraform output -raw vpc_id)
    SUBNET_IDS=$(terraform output -json private_subnet_ids | jq -r '.[]' | tr '\n' ',' | sed 's/,$//')
    cd ..
    
    # Check if service exists
    if aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION &> /dev/null; then
        log_info "Updating existing service..."
        aws ecs update-service \
            --cluster $ECS_CLUSTER \
            --service $ECS_SERVICE \
            --task-definition $APP_NAME-task \
            --region $AWS_REGION
    else
        log_info "Creating new service..."
        aws ecs create-service \
            --cluster $ECS_CLUSTER \
            --service-name $ECS_SERVICE \
            --task-definition $APP_NAME-task \
            --desired-count 2 \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$(aws ec2 describe-security-groups --filters Name=group-name,Values=$APP_NAME-ecs-* --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION)],assignPublicIp=DISABLED}" \
            --load-balancers "targetGroupArn=$(aws elbv2 describe-target-groups --names $APP_NAME-tg --query 'TargetGroups[0].TargetGroupArn' --output text --region $AWS_REGION),containerName=$APP_NAME-container,containerPort=8000" \
            --region $AWS_REGION
    fi
}

# Verify secrets exist in AWS Systems Manager Parameter Store
verify_secrets() {
    log_info "Verifying required secrets in Parameter Store..."
    
    local missing_secrets=()
    
    # Check Django secret key
    if ! aws ssm get-parameter --name "/plantcon/secret-key" --region $AWS_REGION &> /dev/null; then
        missing_secrets+=("/plantcon/secret-key")
    fi
    
    # Check database password
    if ! aws ssm get-parameter --name "/plantcon/db-password" --region $AWS_REGION &> /dev/null; then
        missing_secrets+=("/plantcon/db-password")
    fi
    
    if [ ${#missing_secrets[@]} -ne 0 ]; then
        log_error "Missing required secrets in Parameter Store:"
        for secret in "${missing_secrets[@]}"; do
            log_error " - $secret"
        done
        log_error "Please store these secrets using AWS Console or CLI"
        exit 1
    fi
    
    log_info "All required secrets verified in Parameter Store"
}

# Main deployment function
main() {
    log_info "Starting deployment of $APP_NAME to AWS..."
    
    check_prerequisites
    create_ecr_repository
    IMAGE_URI=$(build_and_push_image)
    deploy_infrastructure
    create_task_definition $IMAGE_URI
    deploy_service
    
    log_info "Deployment completed successfully!"
    
    cd deploy
    ALB_DNS=$(terraform output -raw alb_dns_name)
    cd ..
    
    log_info "Application URL: http://$ALB_DNS"
    log_info "Run database migrations:"
    log_info "1. Connect to ECS container"
    log_info "2. Run: python manage.py migrate"
    log_info "3. Run: python manage.py collectstatic --noinput"
    log_info "4. Create superuser: python manage.py createsuperuser"
    log_info "Monitor deployment: aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE --region $AWS_REGION"
}

# Run main function
main "$@"