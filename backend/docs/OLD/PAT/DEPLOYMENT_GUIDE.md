# Physical Activity Tracking (PAT) Service Deployment Guide

This guide provides instructions for deploying the Physical Activity Tracking (PAT) service to AWS within the Concierge Psychiatry Platform.

## Architecture Overview

The PAT service is designed with the following components:

1. **AWS SageMaker** - Hosts the machine learning model for actigraphy analysis
2. **Amazon S3** - Stores raw actigraphy data and analysis results
3. **Amazon DynamoDB** - Stores metadata, analysis records, and embeddings
4. **AWS Comprehend Medical** - Used for PHI detection and sanitization
5. **API Layer** - FastAPI endpoints deployed via AWS Lambda and API Gateway

## Prerequisites

- AWS Account with HIPAA BAA in place
- AWS CLI configured with appropriate credentials
- Python 3.9+ and pip
- Terraform 1.0+ (for infrastructure deployment)

## Deployment Steps

### 1. Set Up Environment Variables

Create a `.env.production` file with the necessary configuration:

```
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=novamind-prod

# PAT Service Configuration
PAT_SERVICE_TYPE=aws
PAT_ENDPOINT_NAME=novamind-pat-endpoint
PAT_BUCKET_NAME=novamind-pat-data
PAT_ANALYSES_TABLE=novamind-pat-analyses
PAT_EMBEDDINGS_TABLE=novamind-pat-embeddings
PAT_INTEGRATIONS_TABLE=novamind-pat-integrations

# SageMaker Configuration
SAGEMAKER_INSTANCE_TYPE=ml.g4dn.xlarge
SAGEMAKER_MODEL_DATA_URL=s3://novamind-models/pat/model.tar.gz
```

### 2. Deploy Infrastructure

The Terraform scripts for infrastructure deployment are in the `infrastructure/aws/pat` directory:

```bash
cd infrastructure/aws/pat
terraform init
terraform apply
```

This will create:
- S3 buckets for data storage
- DynamoDB tables for metadata
- IAM roles and policies
- SageMaker model and endpoint

### 3. Deploy Model to SageMaker

Use the provided script to deploy the PAT model to SageMaker:

```bash
python scripts/deploy_pat_model.py
```

This script:
1. Uploads the model artifacts to S3
2. Creates a SageMaker model
3. Creates a SageMaker endpoint configuration
4. Creates a SageMaker endpoint

### 4. Configure the Application

Update the application configuration to use the AWS implementation:

```bash
# In your application settings
export PAT_SERVICE_TYPE=aws
```

### 5. Test the Deployment

Run the integration tests against the production environment:

```bash
# Set environment to production
export ENV=production

# Run integration tests
pytest tests/integration/api/test_actigraphy_api_integration.py
```

## Security Considerations

### HIPAA Compliance

- All data in S3 is encrypted at rest using AWS KMS
- DynamoDB tables are encrypted at rest
- All network traffic is encrypted in transit using TLS 1.2+
- PHI is sanitized before processing using AWS Comprehend Medical
- Access is controlled using IAM roles and policies
- SageMaker endpoints are deployed in a VPC with Security Groups

### Access Control

- API endpoints require authentication using JWT tokens
- Requests are authorized based on user roles and patient associations
- API Gateway has WAF protection enabled

## Monitoring and Logging

- CloudWatch Logs for API Gateway and Lambda
- CloudWatch Metrics for SageMaker endpoint performance
- CloudTrail for API calls and administrative actions
- SageMaker Model Monitor for drift detection

## Troubleshooting

### Common Issues

1. **SageMaker Endpoint Creation Fails**
   - Check IAM roles have sufficient permissions
   - Verify model artifacts are correctly packaged
   - Check instance type availability in your region

2. **Performance Issues**
   - Scale SageMaker endpoint to a larger instance type
   - Enable auto-scaling for SageMaker endpoints
   - Use SageMaker Multi-Model Endpoints for cost optimization

3. **Data Access Issues**
   - Verify IAM policies for S3 and DynamoDB
   - Check VPC configuration for SageMaker endpoints

## Cost Optimization

- Use Spot Instances for development/staging environments
- Set up auto-scaling for SageMaker endpoints
- Use S3 Intelligent-Tiering for infrequently accessed data
- Configure DynamoDB with appropriate read/write capacity

## Backup and Disaster Recovery

- DynamoDB Point-in-time Recovery is enabled
- S3 bucket versioning is enabled
- Regular backups of configuration to S3
- Multi-region deployment for high availability

## Maintenance

### Updates and Patches

- Model updates are deployed through CI/CD pipeline
- Infrastructure updates are managed through Terraform
- Security patches are applied automatically

### Scaling

- SageMaker endpoints can be scaled horizontally or vertically
- DynamoDB can be scaled with on-demand capacity

## Support

For issues or questions, contact:
- DevOps Team: devops@novamind.com
- Data Science Team: datascience@novamind.com