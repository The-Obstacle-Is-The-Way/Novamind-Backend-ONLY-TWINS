# DEPLOYMENT AND CI/CD PIPELINE

## Overview

This document outlines the deployment process and CI/CD pipeline for the NOVAMIND platform. It provides a comprehensive guide to deploying the application to production and setting up a continuous integration and continuous deployment pipeline.

## 1. Deployment Architecture

The NOVAMIND platform is deployed using a containerized approach with AWS services:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AWS Cloud                                     │
│                                                                         │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐          │
│  │   AWS Route53 │────▶ AWS CloudFront │────▶   AWS S3      │          │
│  │   (DNS)       │     │   (CDN)       │     │   (Frontend)  │          │
│  └───────────────┘     └───────────────┘     └───────────────┘          │
│          │                                                              │
│          │                                                              │
│          ▼                                                              │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐          │
│  │   AWS ALB     │────▶   AWS ECS      │────▶   AWS ECR     │          │
│  │   (Load       │     │   (Fargate)    │     │   (Container │          │
│  │   Balancer)   │     │                │     │   Registry)  │          │
│  └───────────────┘     └───────────────┘     └───────────────┘          │
│          │                     │                                        │
│          │                     │                                        │
│          ▼                     ▼                                        │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐          │
│  │   AWS RDS     │◀────▶   AWS S3     │◀────▶ AWS Cognito  │          │
│  │   (PostgreSQL)│     │   (Storage)   │     │   (Auth)      │          │
│  └───────────────┘     └───────────────┘     └───────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Frontend**: Hosted on AWS S3 and served through CloudFront CDN.
2. **Backend API**: Containerized FastAPI application running on AWS ECS Fargate.
3. **Database**: PostgreSQL database hosted on AWS RDS.
4. **Authentication**: AWS Cognito for user authentication and authorization.
5. **Storage**: AWS S3 for file storage.
6. **Load Balancing**: AWS Application Load Balancer (ALB) for routing traffic to the backend.
7. **DNS**: AWS Route53 for domain name management.

## 2. Deployment Process

### 2.1. Infrastructure as Code

The infrastructure is defined using AWS CloudFormation or Terraform:

```yaml
# terraform/main.tf (example)

provider "aws" {
  region = var.aws_region
}

# VPC and Networking
module "vpc" {
  source = "./modules/vpc"
  # ...
}

# ECS Cluster
module "ecs" {
  source = "./modules/ecs"
  vpc_id = module.vpc.vpc_id
  # ...
}

# RDS Database
module "rds" {
  source = "./modules/rds"
  vpc_id = module.vpc.vpc_id
  # ...
}

# S3 Bucket
module "s3" {
  source = "./modules/s3"
  # ...
}

# Cognito User Pool
module "cognito" {
  source = "./modules/cognito"
  # ...
}

# CloudFront Distribution
module "cloudfront" {
  source = "./modules/cloudfront"
  s3_bucket_id = module.s3.bucket_id
  # ...
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  vpc_id = module.vpc.vpc_id
  # ...
}

# Route53 DNS
module "route53" {
  source = "./modules/route53"
  domain_name = var.domain_name
  # ...
}
```

### 2.2. Docker Image

The application is containerized using Docker:

```dockerfile
# Dockerfile

# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.3. Database Migrations

Database migrations are handled using Alembic:

```bash
# Run migrations
alembic upgrade head
```

### 2.4. Environment Variables

Environment variables are managed using AWS Systems Manager Parameter Store or AWS Secrets Manager:

```bash
# Retrieve environment variables
aws ssm get-parameters-by-path --path /novamind/production/ --recursive --with-decryption
```

## 3. CI/CD Pipeline

The CI/CD pipeline is implemented using AWS CodePipeline and AWS CodeBuild:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       CI/CD Pipeline                                    │
│                                                                         │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐          │
│  │   Source      │────▶   Build        │────▶   Test         │          │
│  │   (GitHub)    │     │   (CodeBuild) │     │   (CodeBuild) │          │
│  └───────────────┘     └───────────────┘     └───────────────┘          │
│          │                                           │                  │
│          │                                           │                  │
│          ▼                                           ▼                  │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐          │
│  │   Deploy      │◀────┤   Approval    │◀────┤   Security    │          │
│  │   (CodeDeploy)│     │   (Manual)    │     │   Scan        │          │
│  └───────────────┘     └───────────────┘     └───────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.1. Pipeline Configuration

The pipeline is defined using AWS CloudFormation or Terraform:

```yaml
# terraform/modules/pipeline/main.tf (example)

resource "aws_codepipeline" "pipeline" {
  name     = "novamind-pipeline"
  role_arn = aws_iam_role.pipeline_role.arn

  artifact_store {
    location = aws_s3_bucket.artifact_bucket.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeStarSourceConnection"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        ConnectionArn    = aws_codestarconnections_connection.github.arn
        FullRepositoryId = var.repository_id
        BranchName       = var.branch_name
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "BuildAndTest"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]

      configuration = {
        ProjectName = aws_codebuild_project.build.name
      }
    }
  }

  stage {
    name = "Test"

    action {
      name             = "UnitTests"
      category         = "Test"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["build_output"]
      output_artifacts = ["test_output"]

      configuration = {
        ProjectName = aws_codebuild_project.test.name
      }
    }
  }

  stage {
    name = "SecurityScan"

    action {
      name             = "SecurityScan"
      category         = "Test"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["build_output"]
      output_artifacts = ["security_output"]

      configuration = {
        ProjectName = aws_codebuild_project.security.name
      }
    }
  }

  stage {
    name = "Approval"

    action {
      name     = "Approval"
      category = "Approval"
      owner    = "AWS"
      provider = "Manual"
      version  = "1"
    }
  }

  stage {
    name = "Deploy"

    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ECS"
      version         = "1"
      input_artifacts = ["build_output"]

      configuration = {
        ClusterName = var.ecs_cluster_name
        ServiceName = var.ecs_service_name
      }
    }
  }
}
```

### 3.2. Build Specification

The build process is defined in a `buildspec.yml` file:

```yaml
# buildspec.yml

version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.11
    commands:
      - echo Installing dependencies...
      - pip install -r requirements.txt
      - pip install -r requirements-dev.txt
  
  pre_build:
    commands:
      - echo Running linters and formatters...
      - black --check app/ tests/
      - isort --check-only app/ tests/
      - flake8 app/ tests/
      - mypy app/ tests/
      - bandit -r app/
  
  build:
    commands:
      - echo Building the Docker image...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI
      - docker build -t $ECR_REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION .
      - docker tag $ECR_REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION $ECR_REPOSITORY_URI:latest
  
  post_build:
    commands:
      - echo Running tests...
      - pytest tests/ --cov=app --cov-report=xml
      - echo Pushing the Docker image...
      - docker push $ECR_REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION
      - docker push $ECR_REPOSITORY_URI:latest
      - echo Writing image definitions file...
      - aws ecs describe-task-definition --task-definition $ECS_TASK_DEFINITION --query taskDefinition > task-definition.json
      - envsubst < task-definition.json > task-definition-updated.json
      - aws ecs register-task-definition --cli-input-json file://task-definition-updated.json

artifacts:
  files:
    - task-definition-updated.json
    - appspec.yml
    - coverage.xml
  discard-paths: yes

cache:
  paths:
    - '/root/.cache/pip/**/*'
```

### 3.3. Deployment Specification

The deployment process is defined in an `appspec.yml` file:

```yaml
# appspec.yml

version: 0.0
Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: <TASK_DEFINITION>
        LoadBalancerInfo:
          ContainerName: "novamind-api"
          ContainerPort: 8000
```

## 4. Monitoring and Logging

### 4.1. CloudWatch Logs

Application logs are sent to CloudWatch Logs:

```python
# app/infrastructure/logging/logger.py

import logging
import watchtower
import boto3

def setup_logging():
    """Set up logging with CloudWatch integration"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Add CloudWatch handler
    cloudwatch_handler = watchtower.CloudWatchLogHandler(
        log_group="novamind-logs",
        stream_name="api-logs",
        boto3_session=boto3.Session()
    )
    logger.addHandler(cloudwatch_handler)
    
    return logger
```

### 4.2. CloudWatch Alarms

CloudWatch Alarms are set up to monitor the application:

```yaml
# terraform/modules/monitoring/main.tf (example)

resource "aws_cloudwatch_metric_alarm" "api_errors" {
  alarm_name          = "novamind-api-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/ECS"
  period              = "60"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "This metric monitors API errors"
  
  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

### 4.3. X-Ray Tracing

AWS X-Ray is used for distributed tracing:

```python
# app/main.py

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

# Set up X-Ray
xray_recorder.configure(service='novamind-api')
app.add_middleware(XRayMiddleware, recorder=xray_recorder)
```

## 5. Scaling and High Availability

### 5.1. Auto Scaling

The application is configured to scale automatically based on load:

```yaml
# terraform/modules/ecs/main.tf (example)

resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.main.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_policy_cpu" {
  name               = "cpu-auto-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

### 5.2. Multi-AZ Deployment

The application is deployed across multiple Availability Zones for high availability:

```yaml
# terraform/modules/ecs/main.tf (example)

resource "aws_ecs_service" "main" {
  name            = "novamind-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnets
    security_groups = [aws_security_group.ecs.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "novamind-api"
    container_port   = 8000
  }

  deployment_controller {
    type = "ECS"
  }

  lifecycle {
    ignore_changes = [desired_count]
  }
}
```

## 6. Disaster Recovery

### 6.1. Database Backups

Automated database backups are configured:

```yaml
# terraform/modules/rds/main.tf (example)

resource "aws_db_instance" "main" {
  # ...
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "mon:04:00-mon:05:00"
  # ...
}
```

### 6.2. S3 Versioning

S3 bucket versioning is enabled for file storage:

```yaml
# terraform/modules/s3/main.tf (example)

resource "aws_s3_bucket" "main" {
  bucket = "novamind-files"
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  
  versioning_configuration {
    status = "Enabled"
  }
}
```

## 7. Security

### 7.1. Security Groups

Security groups are configured to restrict access:

```yaml
# terraform/modules/ecs/main.tf (example)

resource "aws_security_group" "ecs" {
  name        = "novamind-ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    security_groups = [var.alb_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### 7.2. IAM Roles

IAM roles are configured with least privilege:

```yaml
# terraform/modules/ecs/main.tf (example)

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "novamind-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
```

### 7.3. WAF

AWS WAF is configured to protect against common web exploits:

```yaml
# terraform/modules/waf/main.tf (example)

resource "aws_wafv2_web_acl" "main" {
  name        = "novamind-waf"
  description = "WAF for NOVAMIND API"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "novamind-waf"
    sampled_requests_enabled   = true
  }
}
```

## 8. Rollback Strategy

### 8.1. Blue-Green Deployment

Blue-green deployment is used for zero-downtime deployments:

```yaml
# terraform/modules/ecs/main.tf (example)

resource "aws_ecs_service" "main" {
  # ...
  deployment_controller {
    type = "CODE_DEPLOY"
  }
  # ...
}
```

### 8.2. Automated Rollback

Automated rollback is configured in case of deployment failures:

```yaml
# buildspec.yml

version: 0.2

phases:
  # ...
  post_build:
    commands:
      # ...
      - |
        if [ $CODEBUILD_BUILD_SUCCEEDING -eq 0 ]; then
          echo "Build failed, rolling back..."
          aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --task-definition $PREVIOUS_TASK_DEFINITION
        fi
      # ...
```

## Conclusion

This deployment and CI/CD pipeline guide provides a comprehensive approach to deploying the NOVAMIND platform to production. By following these guidelines, you can ensure a reliable, secure, and scalable deployment process.