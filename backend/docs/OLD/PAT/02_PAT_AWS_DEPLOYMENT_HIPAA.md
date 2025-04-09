# PAT AWS Deployment with HIPAA Compliance

## Overview

This document outlines the AWS deployment architecture for the Pretrained Actigraphy Transformer (PAT) service, ensuring HIPAA compliance for handling sensitive patient biometric data. The deployment follows a containerized microservice approach with GPU acceleration for optimal performance.

## HIPAA-Compliant AWS Architecture

### Core Services and Configuration

1. **Compute Resources**:
   - **Amazon EC2 with GPU instances** (G4dn or G5 family with NVIDIA Tesla GPUs)
   - AWS Deep Learning AMI with pre-installed NVIDIA drivers, CUDA, and ML frameworks
   - Instances deployed in private subnets within a VPC
   - Auto Scaling Groups for high availability and load management

2. **Containerization and Orchestration**:
   - **Amazon ECS/EKS** for container orchestration
   - GPU-enabled task definitions with NVIDIA Container Toolkit integration
   - Multi-AZ deployment for high availability
   - Private ECR repository for container images

3. **Storage and Databases**:
   - **Amazon S3** with server-side encryption (SSE-KMS) for:
     - Model weights storage
     - Raw actigraphy data (encrypted at rest)
     - Analysis results for long-term storage
   - **Amazon DynamoDB** with encryption for:
     - Patient biometric profiles
     - Analysis results and metrics
     - Time-series data indexing
   - **Amazon RDS** (PostgreSQL) with encryption for:
     - Relational data storage
     - Patient-provider relationships
     - Structured clinical data

4. **Networking and Security**:
   - **VPC** with private and public subnets
   - **Network ACLs** and **Security Groups** with least privilege access
   - **AWS PrivateLink** for private service connections
   - **VPC Endpoints** for S3 and DynamoDB access without internet exposure
   - **Application Load Balancer** with TLS termination and WebSocket support
   - **AWS WAF** for API protection

5. **Identity and Access Management**:
   - **IAM Roles** with least privilege permissions
   - **Service-specific IAM roles** for each microservice
   - **Resource-based policies** for S3 buckets and other resources
   - **AWS Secrets Manager** for storing credentials and configuration

6. **Monitoring and Logging**:
   - **CloudWatch** for metrics, logs, and alarms
   - **CloudTrail** for API activity auditing
   - **AWS Config** for configuration compliance
   - **AWS Security Hub** for security posture monitoring
   - **Custom logging** with PHI sanitization

## Deployment Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             AWS Cloud                                    │
│                                                                         │
│  ┌─────────────┐     ┌──────────────┐      ┌────────────────────────┐   │
│  │             │     │              │      │                        │   │
│  │ Application │     │  API Gateway │      │  CloudFront            │   │
│  │    Load     │────▶│   (HTTPS)    │◀────▶│  (Web Application)     │   │
│  │  Balancer   │     │              │      │                        │   │
│  │             │     └──────────────┘      └────────────────────────┘   │
│  └─────────────┘              │                        │                │
│         │                     │                        │                │
│         ▼                     ▼                        ▼                │
│  ┌─────────────┐     ┌──────────────┐      ┌────────────────────────┐   │
│  │             │     │              │      │                        │   │
│  │    VPC      │     │  CloudWatch  │      │  S3 Buckets            │   │
│  │  (Private   │     │   Logs &     │      │  (Encrypted at rest)   │   │
│  │  Subnets)   │     │   Metrics    │      │                        │   │
│  └─────────────┘     └──────────────┘      └────────────────────────┘   │
│         │                                             │                │
│         ▼                                             │                │
│  ┌──────────────────────────────────────────┐         │                │
│  │           ECS/EKS Cluster                │         │                │
│  │                                          │         │                │
│  │  ┌─────────────┐    ┌─────────────┐     │         │                │
│  │  │             │    │             │     │         │                │
│  │  │ PAT Service │    │ MentalLLaMA │     │         │                │
│  │  │ Container   │    │  Service    │     │         │                │
│  │  │ (GPU)       │    │             │     │         │                │
│  │  └─────────────┘    └─────────────┘     │         │                │
│  │         │                  │            │         │                │
│  │         ▼                  ▼            │         │                │
│  │  ┌─────────────┐    ┌─────────────┐     │         │                │
│  │  │             │    │             │     │         │                │
│  │  │ Other ML    │    │ Digital Twin│     │         │                │
│  │  │ Services    │    │ Integration │     │         │                │
│  │  │             │    │ Service     │     │         │                │
│  │  └─────────────┘    └─────────────┘     │         │                │
│  └──────────────────────────────────────────┘         │                │
│         │                                             │                │
│         ▼                                             ▼                │
│  ┌─────────────┐                           ┌────────────────────────┐   │
│  │             │                           │                        │   │
│  │  DynamoDB   │                           │  Secrets Manager       │   │
│  │  Tables     │                           │  (Credentials)         │   │
│  │  (Encrypted)│                           │                        │   │
│  └─────────────┘                           └────────────────────────┘   │
│         │                                             │                │
│         ▼                                             ▼                │
│  ┌─────────────┐                           ┌────────────────────────┐   │
│  │             │                           │                        │   │
│  │  RDS        │                           │  CloudTrail            │   │
│  │  (Encrypted)│                           │  (Audit Logs)          │   │
│  │             │                           │                        │   │
│  └─────────────┘                           └────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## HIPAA Compliance Considerations

### Data Encryption

1. **Data at Rest**:
   - S3 buckets configured with SSE-KMS encryption
   - DynamoDB tables with encryption enabled
   - RDS instances with encryption enabled
   - EBS volumes encrypted with KMS keys
   - Model weights encrypted in S3 or container images

2. **Data in Transit**:
   - TLS 1.2+ for all API communications
   - VPC traffic encryption for inter-service communication
   - HTTPS for all external endpoints
   - API Gateway with TLS termination

### Access Controls

1. **Authentication and Authorization**:
   - JWT-based authentication for all API endpoints
   - Role-based access control (RBAC) for all services
   - IAM roles with least privilege principle
   - Multi-factor authentication (MFA) for administrative access

2. **Audit and Monitoring**:
   - CloudTrail enabled for all regions
   - CloudWatch Logs with retention policies
   - Custom audit logging for PHI access
   - Regular access reviews and monitoring

### Business Associate Agreement (BAA)

- AWS BAA in place covering all used services
- Documentation of HIPAA-eligible services used
- Regular compliance reviews and updates

## Container Configuration for PAT

### Docker Configuration

```dockerfile
# Base image with GPU support
FROM tensorflow/tensorflow:2.18.0-gpu

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app/
WORKDIR /app

# Download model weights at build time or mount at runtime
RUN mkdir -p /app/models
# Either:
# COPY ./models/PAT-M.h5 /app/models/
# Or use ENV variable to download at startup

# Set environment variables
ENV MODEL_PATH=/app/models/PAT-M.h5
ENV TF_FORCE_GPU_ALLOW_GROWTH=true
ENV LOG_LEVEL=INFO

# Non-root user for security
RUN useradd -m appuser
USER appuser

# Expose port for FastAPI
EXPOSE 8000

# Start the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### ECS Task Definition

```json
{
  "family": "pat-service",
  "networkMode": "awsvpc",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/PATServiceRole",
  "containerDefinitions": [
    {
      "name": "pat-service",
      "image": "ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/pat-service:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pat-service",
          "awslogs-region": "REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "environment": [
        {
          "name": "S3_BUCKET",
          "value": "novamind-models"
        },
        {
          "name": "MODEL_KEY",
          "value": "models/PAT-M.h5"
        }
      ],
      "secrets": [
        {
          "name": "AWS_ACCESS_KEY_ID",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:pat/aws-credentials:AWS_ACCESS_KEY_ID::"
        },
        {
          "name": "AWS_SECRET_ACCESS_KEY",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:pat/aws-credentials:AWS_SECRET_ACCESS_KEY::"
        }
      ],
      "resourceRequirements": [
        {
          "type": "GPU",
          "value": "1"
        }
      ],
      "ulimits": [
        {
          "name": "nofile",
          "softLimit": 65536,
          "hardLimit": 65536
        }
      ]
    }
  ],
  "requiresCompatibilities": [
    "FARGATE",
    "EC2"
  ],
  "cpu": "4096",
  "memory": "16384"
}
```

## Scaling and High Availability

1. **Auto Scaling**:
   - ECS Service Auto Scaling based on CPU/GPU utilization
   - Target tracking scaling policies
   - Scheduled scaling for predictable load patterns

2. **Multi-AZ Deployment**:
   - Services deployed across multiple Availability Zones
   - Database replicas in different AZs
   - Load balancer with cross-zone load balancing

3. **Disaster Recovery**:
   - Regular backups of databases and configurations
   - Cross-region replication for critical data
   - Documented recovery procedures

## Cost Optimization

1. **Resource Sizing**:
   - Right-sized GPU instances based on model requirements
   - Spot Instances for non-critical workloads
   - Reserved Instances for predictable workloads

2. **Scaling Policies**:
   - Scale down during low-usage periods
   - Batch processing for non-urgent analyses

3. **Storage Tiering**:
   - S3 Intelligent Tiering for infrequently accessed data
   - DynamoDB on-demand capacity for variable workloads

## Implementation Checklist

- [ ] Create VPC with appropriate subnets and security groups
- [ ] Set up IAM roles and policies
- [ ] Create ECR repository for container images
- [ ] Build and push PAT container image
- [ ] Configure S3 buckets with encryption
- [ ] Set up DynamoDB tables with encryption
- [ ] Create ECS/EKS cluster with GPU support
- [ ] Deploy PAT service with appropriate task definition
- [ ] Configure load balancer and target groups
- [ ] Set up CloudWatch monitoring and alerting
- [ ] Enable CloudTrail and AWS Config
- [ ] Implement backup and disaster recovery procedures
- [ ] Conduct security assessment and penetration testing
- [ ] Document HIPAA compliance measures

## Related Documentation

- [01_PAT_ARCHITECTURE_AND_INTEGRATION.md](01_PAT_ARCHITECTURE_AND_INTEGRATION.md)
- [03_PAT_IMPLEMENTATION_GUIDE.md](03_PAT_IMPLEMENTATION_GUIDE.md)
- [04_PAT_MICROSERVICE_API.md](04_PAT_MICROSERVICE_API.md)
- [HIPAA-SECURITY-ENVIRONMENT.md](../HIPAA-SECURITY-ENVIRONMENT.md)
- [AWS_DEPLOYMENT_HIPAA.md](../MentalLLaMA/02_AWS_DEPLOYMENT_HIPAA.md)