# Plantcon AWS Deployment Guide

## 🚨 CRITICAL: Security Fixes Applied

The following critical security vulnerabilities have been fixed:

1. **CSV Import Vulnerability**: Added proper validation and authorization
2. **Input Validation**: Added decimal validation for financial amounts
3. **Production Settings**: Separated development and production configurations
4. **Security Headers**: Added comprehensive security headers for production

## Prerequisites

Before deploying to AWS, ensure you have:

### Required Tools
- AWS CLI configured with appropriate permissions
- Docker installed and running
- Terraform installed (>= 1.0)
- Valid AWS account with necessary permissions

### Required AWS Permissions
Your AWS user/role needs permissions for:
- ECS (Elastic Container Service)
- RDS (Relational Database Service)
- S3 (Simple Storage Service)
- VPC (Virtual Private Cloud)
- ALB (Application Load Balancer)
- Systems Manager Parameter Store
- CloudWatch Logs

## Pre-Deployment Setup

### 1. Update Environment Variables

Create production environment variables:

```bash
# Copy the template
cp .env.production .env

# Edit .env with your production values
nano .env
```

Required variables (non-sensitive only):
```bash
DJANGO_ENVIRONMENT=production
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-unique-bucket-name
DJANGO_ALLOWED_HOST=yourdomain.com
```

Note: Sensitive values like SITE_SECRET_KEY and RDS_PASSWORD are now stored securely in AWS Parameter Store.

### 2. Generate Strong Secret Key

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Set Deployment Variables

```bash
export DB_PASSWORD="your-secure-database-password"
export SITE_SECRET_KEY="your-generated-secret-key"
```

## Deployment Process

### Automated Deployment

Run the automated deployment script:

```bash
cd deploy
chmod +x deploy.sh
./deploy.sh
```

This script will:
1. Check prerequisites
2. Create AWS infrastructure with Terraform
3. Build and push Docker image to ECR
4. Deploy ECS service
5. Configure load balancer

### Manual Deployment Steps

If you prefer manual deployment:

#### 1. Deploy Infrastructure

```bash
cd deploy
terraform init
terraform plan -var="db_password=$DB_PASSWORD"
terraform apply -var="db_password=$DB_PASSWORD"
```

#### 2. Build and Push Docker Image

```bash
# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"

# Create ECR repository
aws ecr create-repository --repository-name plantcon --region $REGION

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build and push
docker build -t plantcon .
docker tag plantcon:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/plantcon:latest
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/plantcon:latest
```

#### 3. Deploy ECS Service

Use the AWS Console or CLI to create ECS service with the provided task definition.

## Post-Deployment Tasks

### 1. Run Database Migrations (Required)

Connect to your ECS container and run:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 2. Test Application

1. Access your application via the ALB DNS name
2. Test login functionality
3. Verify database connections
4. Test CSV import with small sample
5. Monitor CloudWatch logs

### 3. Configure Domain (Optional)

1. Point your domain to the ALB DNS name
2. Configure SSL certificate in AWS Certificate Manager
3. Update ALB listener to use HTTPS

## Monitoring and Maintenance

### Health Checks

The application includes a health check endpoint at `/health/` that:
- Checks database connectivity
- Returns JSON status
- Used by ALB for health checks

### Logging

Logs are stored in CloudWatch:
- Log Group: `/ecs/plantcon`
- Application logs include security events
- Database query logs (in development)

### Security Monitoring

Monitor for:
- Failed login attempts
- CSV import activities
- Database connection errors
- Unusual financial data modifications

## Rollback Procedure

If deployment fails:

1. **Immediate**: Revert ECS service to previous task definition
2. **Database**: Use RDS automated backups if needed
3. **Infrastructure**: Use `terraform destroy` and redeploy

```bash
# Rollback ECS service
aws ecs update-service --cluster plantcon-cluster --service plantcon-service --task-definition plantcon-task:PREVIOUS_REVISION

# Rollback infrastructure
cd deploy
terraform destroy -var="db_password=$DB_PASSWORD"
```

## Cost Optimization

### Current Resources
- RDS t3.micro: ~$15/month
- ECS Fargate: ~$20-30/month
- ALB: ~$16/month
- S3: ~$1-5/month (depending on usage)

**Total estimated cost: $50-70/month**

### Cost Reduction Options
1. Use RDS scheduled snapshots instead of continuous backups
2. Use single AZ deployment for non-critical environments
3. Implement auto-scaling based on CPU usage
4. Use CloudFront CDN for static files

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check RDS security groups
   - Verify environment variables
   - Check subnet configuration

2. **Application Not Starting**
   - Check ECS task logs in CloudWatch
   - Verify environment variables in task definition
   - Check Docker image build

3. **Load Balancer 502 Errors**
   - Check target group health
   - Verify container port mapping
   - Check security group rules

4. **CSV Import Issues**
   - Check file permissions
   - Verify input validation
   - Monitor application logs

### Debug Commands

```bash
# Check ECS service status
aws ecs describe-services --cluster plantcon-cluster --services plantcon-service

# View container logs
aws logs get-log-events --log-group-name /ecs/plantcon --log-stream-name ecs/plantcon-container/TASK_ID

# Check RDS connectivity
aws rds describe-db-instances --db-instance-identifier plantcon-db

# Test health endpoint
curl http://your-alb-dns-name/health/
```

## Security Considerations

### Implemented Security Measures
1. ✅ Fixed CSV import authorization vulnerability
2. ✅ Added input validation for financial data
3. ✅ Enabled security headers (HSTS, XSS protection)
4. ✅ Database encryption at rest
5. ✅ VPC with private subnets for database
6. ✅ Security groups restricting access
7. ✅ Secrets stored in AWS Parameter Store
8. ✅ Removed sensitive information from environment files
9. ✅ Added Parameter Store secret verification in deployment

### Additional Security Recommendations
1. Enable AWS WAF for ALB
2. Set up CloudTrail for audit logging  
3. Configure AWS Config for compliance monitoring
4. Implement backup and disaster recovery procedures
5. Regular security updates and patches
6. Multi-factor authentication for admin users

## Support

For deployment issues:
1. Check CloudWatch logs first
2. Verify all environment variables
3. Test individual components (database, container, load balancer)
4. Review Terraform state for infrastructure issues

Remember to never commit sensitive information to version control and always use AWS Parameter Store for production secrets.