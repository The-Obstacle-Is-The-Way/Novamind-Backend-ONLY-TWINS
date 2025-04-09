# XGBoost Service Deployment Guide

## Introduction

This guide details the process for deploying the XGBoost machine learning service in a HIPAA-compliant production environment. The XGBoost service leverages AWS SageMaker for model hosting, DynamoDB for data persistence, and KMS for encryption, ensuring both high performance and strict compliance with healthcare data security requirements.

## Prerequisites

### AWS Account and Permissions

- AWS account with proper HIPAA Business Associate Agreement (BAA) in place
- IAM role with permissions for:
  - SageMaker (full access)
  - DynamoDB (read/write)
  - KMS (encrypt/decrypt)
  - CloudWatch (logs creation/access)
  - S3 (model storage)

### Infrastructure Requirements

- VPC with private subnets for SageMaker endpoints
- Security groups with appropriate inbound/outbound rules
- AWS KMS key for PHI encryption (FIPS 140-2 compliant)
- AWS Certificate Manager (ACM) certificate for HTTPS connections

## AWS Infrastructure Setup

### 1. Create KMS Key for PHI Encryption

```bash
# Create a customer managed KMS key for PHI encryption
aws kms create-key \
  --description "XGBoost PHI Encryption Key" \
  --key-usage ENCRYPT_DECRYPT \
  --customer-master-key-spec SYMMETRIC_DEFAULT \
  --tags TagKey=Environment,TagValue=Production \
  --tags TagKey=Service,TagValue=XGBoost \
  --tags TagKey=HIPAA,TagValue=PHI

# Note the KeyId from the output for configuration
```

### 2. Create DynamoDB Tables

Create the following DynamoDB tables:

**XGBoost Predictions Table**
```bash
aws dynamodb create-table \
  --table-name xgboost-predictions \
  --attribute-definitions \
    AttributeName=prediction_id,AttributeType=S \
    AttributeName=patient_id,AttributeType=S \
  --key-schema \
    AttributeName=prediction_id,KeyType=HASH \
    AttributeName=patient_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Service,Value=XGBoost \
  --tags Key=Environment,Value=Production \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
  --sse-specification Enabled=true,SSEType=KMS,KMSMasterKeyId=<KMS_KEY_ID>
```

**XGBoost Feature Importance Table**
```bash
aws dynamodb create-table \
  --table-name xgboost-feature-importance \
  --attribute-definitions \
    AttributeName=prediction_id,AttributeType=S \
    AttributeName=patient_id,AttributeType=S \
  --key-schema \
    AttributeName=prediction_id,KeyType=HASH \
    AttributeName=patient_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Service,Value=XGBoost \
  --tags Key=Environment,Value=Production \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
  --sse-specification Enabled=true,SSEType=KMS,KMSMasterKeyId=<KMS_KEY_ID>
```

**XGBoost Integrations Table**
```bash
aws dynamodb create-table \
  --table-name xgboost-integrations \
  --attribute-definitions \
    AttributeName=integration_id,AttributeType=S \
    AttributeName=patient_id,AttributeType=S \
  --key-schema \
    AttributeName=integration_id,KeyType=HASH \
    AttributeName=patient_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Service,Value=XGBoost \
  --tags Key=Environment,Value=Production \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
  --sse-specification Enabled=true,SSEType=KMS,KMSMasterKeyId=<KMS_KEY_ID>
```

**XGBoost Model Info Table**
```bash
aws dynamodb create-table \
  --table-name xgboost-model-info \
  --attribute-definitions \
    AttributeName=model_type,AttributeType=S \
  --key-schema \
    AttributeName=model_type,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Service,Value=XGBoost \
  --tags Key=Environment,Value=Production \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
  --sse-specification Enabled=true,SSEType=KMS,KMSMasterKeyId=<KMS_KEY_ID>
```

### 3. Create S3 Bucket for Model Storage

```bash
# Create bucket with encryption and versioning
aws s3api create-bucket \
  --bucket novamind-xgboost-models \
  --region us-east-1 \
  --acl private

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket novamind-xgboost-models \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket novamind-xgboost-models \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "aws:kms",
          "KMSMasterKeyID": "<KMS_KEY_ID>"
        },
        "BucketKeyEnabled": true
      }
    ]
  }'
```

### 4. Deploy SageMaker Models

For each model type (risk, treatment, outcome), follow these steps:

1. **Upload model files to S3:**
   ```bash
   aws s3 cp ./models/risk_model.tar.gz s3://novamind-xgboost-models/models/risk/
   aws s3 cp ./models/treatment_model.tar.gz s3://novamind-xgboost-models/models/treatment/
   aws s3 cp ./models/outcome_model.tar.gz s3://novamind-xgboost-models/models/outcome/
   ```

2. **Create SageMaker Model:**
   ```bash
   aws sagemaker create-model \
     --model-name xgboost-risk-model \
     --execution-role-arn arn:aws:iam::123456789012:role/SageMakerExecutionRole \
     --primary-container '{
       "Image": "433757028032.dkr.ecr.us-east-1.amazonaws.com/xgboost:latest",
       "ModelDataUrl": "s3://novamind-xgboost-models/models/risk/risk_model.tar.gz",
       "Environment": {
         "SAGEMAKER_MODEL_SERVER_TIMEOUT": "3600"
       }
     }' \
     --vpc-config '{
       "Subnets": ["subnet-0abc123def456789"],
       "SecurityGroupIds": ["sg-0abc123def456789"]
     }' \
     --tags Key=Service,Value=XGBoost
   ```

3. **Create SageMaker Endpoint Configuration:**
   ```bash
   aws sagemaker create-endpoint-config \
     --endpoint-config-name xgboost-risk-endpoint-config \
     --production-variants '{
       "VariantName": "AllTraffic",
       "ModelName": "xgboost-risk-model",
       "InitialInstanceCount": 1,
       "InstanceType": "ml.m5.large",
       "InitialVariantWeight": 1.0
     }' \
     --tags Key=Service,Value=XGBoost
   ```

4. **Create SageMaker Endpoint:**
   ```bash
   aws sagemaker create-endpoint \
     --endpoint-name xgboost-risk-endpoint \
     --endpoint-config-name xgboost-risk-endpoint-config \
     --tags Key=Service,Value=XGBoost
   ```

5. **Repeat for other model types (treatment, outcome).**

## Application Configuration

### Environment Variables

Set the following environment variables in your application deployment environment:

```bash
# Service Configuration
XGBOOST_SERVICE_TYPE=aws
XGBOOST_PREDICTION_TTL_DAYS=90

# AWS Configuration
AWS_REGION=us-east-1
XGBOOST_KMS_KEY_ID=<KMS_KEY_ID>

# DynamoDB Tables
XGBOOST_PREDICTIONS_TABLE=xgboost-predictions
XGBOOST_FEATURE_IMPORTANCE_TABLE=xgboost-feature-importance
XGBOOST_INTEGRATIONS_TABLE=xgboost-integrations
XGBOOST_MODEL_INFO_TABLE=xgboost-model-info

# SageMaker Endpoints
XGBOOST_RISK_ENDPOINT=xgboost-risk-endpoint
XGBOOST_TREATMENT_ENDPOINT=xgboost-treatment-endpoint
XGBOOST_OUTCOME_ENDPOINT=xgboost-outcome-endpoint
```

### Initialization

Ensure your application initializes the XGBoost service using the factory method with environment variables:

```python
from app.core.services.ml.xgboost.factory import create_xgboost_service_from_env

# Initialize service from environment variables
xgboost_service = create_xgboost_service_from_env()
```

## HIPAA Compliance Verification

Before deploying to production, verify HIPAA compliance:

1. **Encryption at Rest**
   - Verify DynamoDB tables use KMS encryption
   - Verify S3 bucket uses KMS encryption
   - Verify KMS key is FIPS 140-2 compliant

2. **Encryption in Transit**
   - Verify all connections use HTTPS/TLS 1.2+
   - Verify VPC security groups restrict traffic appropriately

3. **Access Controls**
   - Verify IAM roles use least privilege
   - Verify authentication and authorization are enforced
   - Verify AWS CloudTrail logging is enabled

4. **Audit Logging**
   - Verify CloudWatch logging is enabled with appropriate retention
   - Verify logs do not contain PHI

5. **Data Sanitization**
   - Verify PHI detection is enabled in all service methods
   - Verify observer notifications sanitize PHI

## Monitoring and Alerts

### CloudWatch Alarms

Set up the following CloudWatch alarms:

1. **SageMaker Endpoint Health**
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name XGBoost-Risk-Endpoint-Unhealthy \
     --alarm-description "Alarm when risk endpoint is unhealthy" \
     --metric-name Invocations \
     --namespace AWS/SageMaker \
     --statistic Sum \
     --period 300 \
     --threshold 0 \
     --comparison-operator LessThanThreshold \
     --dimensions Name=EndpointName,Value=xgboost-risk-endpoint \
     --evaluation-periods 2 \
     --alarm-actions arn:aws:sns:us-east-1:123456789012:xgboost-alerts
   ```

2. **API Error Rates**
   ```bash
   aws cloudwatch put-metric-alarm \
     --alarm-name XGBoost-API-Error-Rate \
     --alarm-description "Alarm when API error rate exceeds threshold" \
     --metric-name 5XXError \
     --namespace AWS/ApiGateway \
     --statistic Average \
     --period 300 \
     --threshold 0.05 \
     --comparison-operator GreaterThanThreshold \
     --dimensions Name=ApiName,Value=novamind-api \
     --evaluation-periods 2 \
     --alarm-actions arn:aws:sns:us-east-1:123456789012:xgboost-alerts
   ```

### Logging

Ensure the following logging is enabled:

1. **Application Logs**
   - Configure logging level to INFO for production
   - Enable log sanitization to prevent PHI leakage
   - Set up log retention policies (minimum 90 days for HIPAA)

2. **CloudTrail**
   - Enable CloudTrail logging for all AWS API calls
   - Store logs in a dedicated S3 bucket with encryption
   - Set up log retention policies

## Backup and Disaster Recovery

### DynamoDB Backups

Enable point-in-time recovery for all DynamoDB tables:

```bash
aws dynamodb update-continuous-backups \
  --table-name xgboost-predictions \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

### Model Backups

Ensure model versioning in S3:

```bash
# List model versions
aws s3api list-object-versions \
  --bucket novamind-xgboost-models \
  --prefix models/risk/
```

### Disaster Recovery Plan

Document the following disaster recovery procedures:

1. **DynamoDB Table Recovery**
   - Instructions for restoring from point-in-time backup
   - RTO (Recovery Time Objective): 1 hour
   - RPO (Recovery Point Objective): 5 minutes

2. **SageMaker Endpoint Recovery**
   - Instructions for creating new endpoints from existing model artifacts
   - RTO: 30 minutes
   - RPO: No data loss (model artifacts versioned in S3)

## Troubleshooting

### Common Issues and Resolutions

1. **SageMaker Endpoint Invocation Failures**
   - Check endpoint status: `aws sagemaker describe-endpoint --endpoint-name xgboost-risk-endpoint`
   - Check CloudWatch logs for endpoint errors
   - Verify IAM roles and permissions

2. **DynamoDB Access Issues**
   - Verify table exists and is active
   - Check IAM role permissions
   - Check encryption configuration

3. **KMS Key Access Issues**
   - Verify key policy allows service roles access
   - Check key status: `aws kms describe-key --key-id <KMS_KEY_ID>`

### Support Contacts

- **Technical Support:** [support@novamind.com](mailto:support@novamind.com)
- **Security Team:** [security@novamind.com](mailto:security@novamind.com)
- **AWS Support:** Open case via AWS console with HIPAA-compliance tag

## Maintenance

### Model Retraining and Deployment

Document the process for model retraining and deployment:

1. Train new model version
2. Package model artifacts and upload to S3
3. Create new SageMaker model from artifacts
4. Create new endpoint configuration
5. Update existing endpoint or create new endpoint
6. Update environment variables if endpoint names change

### Security Updates

Schedule regular security audits and updates:

1. Monthly review of IAM permissions and roles
2. Quarterly review of security groups and network configuration
3. Annual HIPAA compliance audit
4. Regular patching of all dependencies

## Conclusion

This deployment guide provides a comprehensive approach to deploying the XGBoost service in a HIPAA-compliant environment. Follow these instructions to ensure a secure, reliable, and high-performing implementation that meets the stringent requirements of a luxury concierge psychiatry platform.