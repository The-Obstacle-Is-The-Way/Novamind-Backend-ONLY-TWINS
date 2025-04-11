# Deployment Infrastructure

## Overview

This document outlines the deployment infrastructure for the HIPAA-compliant Concierge Psychiatry Platform's Digital Twin MVP. The deployment architecture follows a containerized approach with infrastructure-as-code principles to ensure consistent, secure, and compliant deployments across environments.

## Core Components

### 1. Containerization Strategy

The application is containerized using Docker with a multi-stage build approach to minimize image size and attack surface:

```mermaid
graph TD
    subgraph "Multi-Stage Docker Build"
        BaseBuild[Base Build Image<br>Python 3.11 + Build Tools]
        DependencyStage[Install Dependencies<br>Poetry + Requirements]
        BuildStage[Build Application<br>Compile + Optimize]
        FinalStage[Final Image<br>Python 3.11-slim + App]
        
        BaseBuild --> DependencyStage
        DependencyStage --> BuildStage
        BuildStage --> FinalStage
    end
    
    subgraph "Container Components"
        FASTAPI[FastAPI Application]
        XGBoost[XGBoost Service]
        DigitalTwin[Digital Twin Engine]
        
        FinalStage --> FASTAPI
        FinalStage --> XGBoost
        FinalStage --> DigitalTwin
    end
```

### 2. AWS Infrastructure Architecture

The infrastructure is provisioned and managed using AWS CloudFormation with modular stacks:

```mermaid
graph TD
    VPC[VPC Stack]
    Security[Security Stack]
    Database[Database Stack]
    Cognito[Cognito Stack]
    ECS[ECS Stack]
    S3[S3 Stack]
    CloudWatch[CloudWatch Stack]
    WAF[WAF Stack]
    
    VPC --> Security
    VPC --> Database
    VPC --> ECS
    Security --> Cognito
    Security --> ECS
    Security --> Database
    Security --> S3
    Security --> WAF
    
    subgraph "Application Layer"
        ECS --> ALB[Application Load Balancer]
        ALB --> APIService[API Service]
        ALB --> DigitalTwinService[Digital Twin Service]
        ALB --> XGBoostService[XGBoost Service]
    end
    
    subgraph "Data Layer"
        Database --> RDS[PostgreSQL RDS]
        S3 --> ModelBucket[ML Models Bucket]
        S3 --> AssetsBucket[Assets Bucket]
        S3 --> BackupBucket[Backup Bucket]
    end
    
    subgraph "Monitoring & Logging"
        CloudWatch --> Logs[CloudWatch Logs]
        CloudWatch --> Metrics[CloudWatch Metrics]
        CloudWatch --> Alarms[CloudWatch Alarms]
        CloudWatch --> Dashboard[CloudWatch Dashboard]
    end
```

### 3. High Availability & Disaster Recovery

The architecture ensures high availability and disaster recovery capabilities:

```mermaid
graph TD
    subgraph "Region A - Primary"
        ALBN["ALB (us-east-1)"]
        ECS1["ECS Cluster<br>(2+ Availability Zones)"]
        RDS1["RDS Primary<br>(Multi-AZ)"]
        
        ALBN --> ECS1
        ECS1 --> RDS1
    end
    
    subgraph "Region B - DR"
        ALBS["ALB (us-west-2)"]
        ECS2["ECS Cluster<br>(2+ Availability Zones)"]
        RDS2["RDS Replica<br>(Multi-AZ)"]
        
        ALBS --> ECS2
        ECS2 --> RDS2
    end
    
    Route53["Route 53<br>Health Checks + Failover"]
    
    Route53 --> ALBN
    Route53 --> ALBS
    RDS1 --> |"Cross-Region Replication"| RDS2
    
    subgraph "Global Resources"
        CloudFront["CloudFront"]
        S3Global["S3 Cross-Region Replication"]
        
        CloudFront --> ALBN
        CloudFront --> ALBS
    end
```

### 4. CI/CD Pipeline

The continuous integration and delivery pipeline automates testing, building, and deployment:

```mermaid
graph TD
    subgraph "Source Control"
        GitHub["GitHub Repository"]
    end
    
    subgraph "CI/CD Pipeline"
        CodePipeline["AWS CodePipeline"]
        
        subgraph "Build & Test Stage"
            CodeBuild["AWS CodeBuild<br>Test + Docker Build"]
        end
        
        subgraph "Security Scan Stage"
            SecurityHub["AWS Security Hub"]
            SonarQube["SonarQube<br>Code Quality"]
            ECRScan["ECR Image Scan"]
        end
        
        subgraph "Deploy Stage"
            CodeDeploy["AWS CodeDeploy"]
        end
        
        subgraph "Validation Stage"
            IntegrationTests["Integration Tests"]
            ComplianceTests["Compliance Tests"]
        end
    end
    
    subgraph "Infrastructure"
        CloudFormation["CloudFormation<br>Deploy Stacks"]
        ECR["Elastic Container Registry"]
        ECS["ECS Service"]
    end
    
    GitHub --> CodePipeline
    CodePipeline --> CodeBuild
    CodeBuild --> SecurityHub
    CodeBuild --> SonarQube
    CodeBuild --> ECRScan
    SecurityHub --> CodeDeploy
    SonarQube --> CodeDeploy
    ECRScan --> CodeDeploy
    CodeDeploy --> CloudFormation
    CodeDeploy --> ECR
    CloudFormation --> ECS
    ECR --> ECS
    ECS --> IntegrationTests
    IntegrationTests --> ComplianceTests
```

## Infrastructure-as-Code Implementation

### 1. CloudFormation Templates

#### VPC Stack

```yaml
# vpc-stack.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'VPC Stack for Concierge Psychiatry Platform'

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsSupport: true
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub ${AWS::StackName}-VPC

  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: 10.0.1.0/24
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub ${AWS::StackName}-PublicSubnet1

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: 10.0.2.0/24
      MapPublicIpOnLaunch: true
      Tags:
        - Key: Name
          Value: !Sub ${AWS::StackName}-PublicSubnet2

  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs '']
      CidrBlock: 10.0.3.0/24
      Tags:
        - Key: Name
          Value: !Sub ${AWS::StackName}-PrivateSubnet1

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs '']
      CidrBlock: 10.0.4.0/24
      Tags:
        - Key: Name
          Value: !Sub ${AWS::StackName}-PrivateSubnet2

  # Additional network components (IGW, NAT Gateway, Route Tables, etc.)
  # ...

Outputs:
  VpcId:
    Description: 'VPC ID'
    Value: !Ref VPC
    Export:
      Name: !Sub ${AWS::StackName}-VpcId

  PublicSubnet1Id:
    Description: 'Public Subnet 1 ID'
    Value: !Ref PublicSubnet1
    Export:
      Name: !Sub ${AWS::StackName}-PublicSubnet1Id

  # Additional outputs
  # ...
```

#### ECS Stack

```yaml
# ecs-stack.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'ECS Stack for Concierge Psychiatry Platform'

Parameters:
  VpcStackName:
    Type: String
    Description: 'Name of the VPC Stack'
  
  ContainerImage:
    Type: String
    Description: 'URI of the container image'
  
  DesiredCount:
    Type: Number
    Default: 2
    Description: 'Desired count of tasks'

Resources:
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub ${AWS::StackName}-Cluster
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT
      DefaultCapacityProviderStrategy:
        - CapacityProvider: FARGATE
          Weight: 1

  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: !Sub ${AWS::StackName}-Task
      Cpu: 1024
      Memory: 2048
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
      ExecutionRoleArn: !GetAtt ECSExecutionRole.Arn
      TaskRoleArn: !GetAtt ECSTaskRole.Arn
      ContainerDefinitions:
        - Name: api
          Image: !Ref ContainerImage
          Essential: true
          PortMappings:
            - ContainerPort: 8000
              HostPort: 8000
              Protocol: tcp
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-group: !Ref LogGroup
              awslogs-region: !Ref AWS::Region
              awslogs-stream-prefix: ecs
          Environment:
            - Name: AWS_REGION
              Value: !Ref AWS::Region
          Secrets:
            - Name: DATABASE_URL
              ValueFrom: !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/novamind/database-url
            - Name: JWT_SECRET
              ValueFrom: !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/novamind/jwt-secret

  # ECS Roles, Service, Load Balancer, etc.
  # ...

Outputs:
  ServiceUrl:
    Description: 'URL of the service'
    Value: !GetAtt LoadBalancer.DNSName
    Export:
      Name: !Sub ${AWS::StackName}-ServiceUrl
```

### 2. Terraform Modules (Alternative Approach)

For teams more comfortable with Terraform, equivalent infrastructure can be defined using Terraform modules:

```hcl
# main.tf
provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "./modules/vpc"
  
  environment = var.environment
  project_name = var.project_name
  vpc_cidr = var.vpc_cidr
  availability_zones = var.availability_zones
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

module "security" {
  source = "./modules/security"
  
  environment = var.environment
  project_name = var.project_name
  vpc_id = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
}

module "database" {
  source = "./modules/database"
  
  environment = var.environment
  project_name = var.project_name
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  security_group_id = module.security.database_security_group_id
  instance_class = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  database_name = var.database_name
  master_username = var.db_master_username
  # Password provided via environment variable or AWS Secrets Manager
}

module "ecs" {
  source = "./modules/ecs"
  
  environment = var.environment
  project_name = var.project_name
  vpc_id = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id = module.security.ecs_security_group_id
  container_image = var.container_image
  desired_count = var.ecs_desired_count
  database_url = module.database.database_url
  # Other environment variables and secrets
}

# Additional modules (S3, CloudWatch, WAF, etc.)
```

## Docker Implementation

### 1. Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim as base

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

# ---- Dependencies stage ----
FROM base as dependencies

# Install Poetry
RUN pip install --no-cache-dir poetry==1.4.2

# Copy poetry config files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# ---- Builder stage ----
FROM dependencies as builder

# Copy application code
COPY . .

# Build/compile if necessary (e.g., Cython components)
RUN poetry build

# ---- Final stage ----
FROM python:3.11-slim as final

WORKDIR /app

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies and built packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/app ./app
COPY --from=builder /app/alembic.ini ./alembic.ini
COPY --from=builder /app/alembic ./alembic
COPY --from=builder /app/main.py ./main.py

# Create non-root user
RUN addgroup --system app && adduser --system --group app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Run the application with Gunicorn
CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 2. Docker Compose for Local Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=novamind
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: dependencies
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/novamind
      - DEBUG=true
      - SECRET_KEY=devsecretkey
      - ENVIRONMENT=development
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

## CI/CD Pipeline Implementation

### 1. GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install poetry
        poetry config virtualenvs.create false
        poetry install
    
    - name: Lint with flake8
      run: |
        flake8 app tests
    
    - name: Check formatting with black
      run: |
        black --check app tests
    
    - name: Run type checking with mypy
      run: |
        mypy app
    
    - name: Run tests with pytest
      run: |
        pytest --cov=app tests/
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        SECRET_KEY: test_secret_key
        ENVIRONMENT: test
    
    - name: Upload coverage report
      uses: codecov/codecov-action@v3
      with:
        token: ${{ secrets.CODECOV_TOKEN }}
        fail_ci_if_error: true

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ secrets.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image to Amazon ECR
      id: build-image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        ECR_REPOSITORY: novamind-api
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        echo "::set-output name=image::$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"
    
    - name: Trigger security scan
      run: |
        aws ecr start-image-scan --repository-name novamind-api --image-id imageTag=${{ github.sha }}

  deploy-dev:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ secrets.AWS_REGION }}
    
    - name: Update ECS service with new image
      run: |
        aws ecs update-service --cluster novamind-dev-cluster --service novamind-api-service --force-new-deployment

  deploy-prod:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ secrets.AWS_REGION }}
    
    - name: Update ECS service with new image
      run: |
        aws ecs update-service --cluster novamind-prod-cluster --service novamind-api-service --force-new-deployment
```

### 2. AWS CodePipeline (Alternative Approach)

The pipeline can also be defined using AWS CloudFormation for CodePipeline:

```yaml
# codepipeline-stack.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CodePipeline Stack for Concierge Psychiatry Platform'

Parameters:
  GitHubOwner:
    Type: String
    Description: 'GitHub repository owner'
  
  GitHubRepo:
    Type: String
    Description: 'GitHub repository name'
  
  GitHubBranch:
    Type: String
    Default: main
    Description: 'GitHub repository branch'
  
  GitHubToken:
    Type: String
    NoEcho: true
    Description: 'GitHub OAuth token'

Resources:
  ArtifactBucket:
    Type: AWS::S3::Bucket
    Properties:
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256

  CodeBuildServiceRole:
    Type: AWS::IAM::Role
    # Role definition with appropriate permissions
    # ...

  CodePipelineServiceRole:
    Type: AWS::IAM::Role
    # Role definition with appropriate permissions
    # ...

  BuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub ${AWS::StackName}-Build
      ServiceRole: !GetAtt CodeBuildServiceRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_SMALL
        Image: aws/codebuild/amazonlinux2-x86_64-standard:3.0
        PrivilegedMode: true
      Source:
        Type: CODEPIPELINE
        BuildSpec: buildspec.yml

  Pipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      RoleArn: !GetAtt CodePipelineServiceRole.Arn
      ArtifactStore:
        Type: S3
        Location: !Ref ArtifactBucket
      Stages:
        - Name: Source
          Actions:
            - Name: Source
              ActionTypeId:
                Category: Source
                Owner: ThirdParty
                Version: 1
                Provider: GitHub
              Configuration:
                Owner: !Ref GitHubOwner
                Repo: !Ref GitHubRepo
                Branch: !Ref GitHubBranch
                OAuthToken: !Ref GitHubToken
              OutputArtifacts:
                - Name: SourceCode

        - Name: Build
          Actions:
            - Name: BuildAndTest
              ActionTypeId:
                Category: Build
                Owner: AWS
                Version: 1
                Provider: CodeBuild
              Configuration:
                ProjectName: !Ref BuildProject
              InputArtifacts:
                - Name: SourceCode
              OutputArtifacts:
                - Name: BuildOutput

        - Name: Deploy
          Actions:
            - Name: DeployToECS
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Version: 1
                Provider: ECS
              Configuration:
                ClusterName: !ImportValue NovamindECSCluster
                ServiceName: !ImportValue NovamindECSService
              InputArtifacts:
                - Name: BuildOutput

Outputs:
  PipelineUrl:
    Description: 'URL to the CodePipeline console'
    Value: !Sub https://console.aws.amazon.com/codepipeline/home?region=${AWS::Region}#/view/${Pipeline}
```

## Security & Compliance Integration

### 1. AWS Security Hub Integration

```yaml
# security-stack.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Security Stack for Concierge Psychiatry Platform'

Resources:
  SecurityHub:
    Type: AWS::SecurityHub::Hub
    Properties: {}

  SecurityHubStandards:
    Type: AWS::SecurityHub::StandardsSubscription
    Properties:
      StandardsArn: !Sub arn:aws:securityhub:${AWS::Region}::standards/aws-foundational-security-best-practices/v/1.0.0
    DependsOn: SecurityHub

  ConfigRecorder:
    Type: AWS::Config::ConfigurationRecorder
    Properties:
      RecordingGroup:
        AllSupported: true
        IncludeGlobalResourceTypes: true
      RoleARN: !GetAtt ConfigRole.Arn

  ConfigDeliveryChannel:
    Type: AWS::Config::DeliveryChannel
    Properties:
      ConfigSnapshotDeliveryProperties:
        DeliveryFrequency: Six_Hours
      S3BucketName: !Ref ConfigBucket
    DependsOn: ConfigRecorder

  ConfigBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256

  ConfigRole:
    Type: AWS::IAM::Role
    # Role definition with appropriate permissions
    # ...

  # Additional security resources (WAF, GuardDuty, etc.)
```

### 2. Build and Deploy Time Security Checks

```yaml
# buildspec.yml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.11
    commands:
      - pip install poetry
      - poetry config virtualenvs.create false
      - poetry install

  pre_build:
    commands:
      # Security checks
      - poetry run safety check
      - poetry run bandit -r app
      # Dependency vulnerability scanning
      - poetry export -f requirements.txt | poetry run pip-audit
      # HIPAA compliance checks
      - ./scripts/hipaa_compliance_check.sh
      # Unit tests
      - poetry run pytest tests/

  build:
    commands:
      # Build Docker image
      - echo Build started on `date`
      - echo Building the Docker image...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI
      - docker build -t $ECR_REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION .
      - docker tag $ECR_REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION $ECR_REPOSITORY_URI:latest

  post_build:
    commands:
      # Push Docker image
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push $ECR_REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION
      - docker push $ECR_REPOSITORY_URI:latest
      # Create task definition
      - aws ecs describe-task-definition --task-definition $TASK_DEFINITION_NAME | jq '.taskDefinition' > task-definition.json
      - jq '.containerDefinitions[0].image="'$ECR_REPOSITORY_URI:$CODEBUILD_RESOLVED_SOURCE_VERSION'"' task-definition.json > new-task-definition.json
      - aws ecs register-task-definition --cli-input-json file://new-task-definition.json
      # Start security scan
      - aws ecr start-image-scan --repository-name $(echo $ECR_REPOSITORY_URI | cut -d/ -f2) --image-id imageTag=$CODEBUILD_RESOLVED_SOURCE_VERSION
      - echo Waiting for ECR scan to complete...
      - sleep 60
      - aws ecr describe-image-scan-findings --repository-name $(echo $ECR_REPOSITORY_URI | cut -d/ -f2) --image-id imageTag=$CODEBUILD_RESOLVED_SOURCE_VERSION

artifacts:
  files:
    - imagedefinitions.json
    - appspec.yml
    - taskdef.json
```

## Monitoring and Observability

### 1. CloudWatch Dashboard Setup

```yaml
# monitoring-stack.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Monitoring Stack for Concierge Psychiatry Platform'

Resources:
  Dashboard:
    Type: AWS::CloudWatch::Dashboard
    Properties:
      DashboardName: !Sub ${AWS::StackName}-Dashboard
      DashboardBody: !Sub |
        {
          "widgets": [
            {
              "type": "metric",
              "x": 0,
              "y": 0,
              "width": 12,
              "height": 6,
              "properties": {
                "metrics": [
                  [ "AWS/ECS", "CPUUtilization", "ServiceName", "${ECSServiceName}", "ClusterName", "${ECSClusterName}", { "stat": "Average" } ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "${AWS::Region}",
                "title": "ECS CPU Utilization",
                "period": 300
              }
            },
            {
              "type": "metric",
              "x": 12,
              "y": 0,
              "width": 12,
              "height": 6,
              "properties": {
                "metrics": [
                  [ "AWS/ECS", "MemoryUtilization", "ServiceName", "${ECSServiceName}", "ClusterName", "${ECSClusterName}", { "stat": "Average" } ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "${AWS::Region}",
                "title": "ECS Memory Utilization",
                "period": 300
              }
            },
            {
              "type": "metric",
              "x": 0,
              "y": 6,
              "width": 12,
              "height": 6,
              "properties": {
                "metrics": [
                  [ "AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "${DBInstanceIdentifier}", { "stat": "Average" } ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "${AWS::Region}",
                "title": "RDS CPU Utilization",
                "period": 300
              }
            },
            {
              "type": "metric",
              "x": 12,
              "y": 6,
              "width": 12,
              "height": 6,
              "properties": {
                "metrics": [
                  [ "AWS/RDS", "FreeableMemory", "DBInstanceIdentifier", "${DBInstanceIdentifier}", { "stat": "Average" } ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "${AWS::Region}",
                "title": "RDS Freeable Memory",
                "period": 300
              }
            },
            {
              "type": "metric",
              "x": 0,
              "y": 12,
              "width": 24,
              "height": 6,
              "properties": {
                "metrics": [
                  [ "AWS/ApplicationELB", "HTTPCode_Target_2XX_Count", "LoadBalancer", "${LoadBalancerName}" ],
                  [ ".", "HTTPCode_Target_4XX_Count", ".", "." ],
                  [ ".", "HTTPCode_Target_5XX_Count", ".", "." ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "${AWS::Region}",
                "title": "ALB Response Codes",
                "period": 300
              }
            },
            {
              "type": "metric",
              "x": 0,
              "y": 18,
              "width": 24,
              "height": 6,
              "properties": {
                "metrics": [
                  [ "AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "${LoadBalancerName}", { "stat": "p50" } ],
                  [ "...", { "stat": "p90" } ],
                  [ "...", { "stat": "p99" } ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "${AWS::Region}",
                "title": "ALB Response Times",
                "period": 300
              }
            }
          ]
        }

  # Define Alarms for critical metrics
  CPUAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub ${AWS::StackName}-High-CPU
      AlarmDescription: Alarm if CPU exceeds 80% for 5 minutes
      MetricName: CPUUtilization
      Namespace: AWS/ECS
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 80
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: ServiceName
          Value: !Ref ECSServiceName
        - Name: ClusterName
          Value: !Ref ECSClusterName
      AlarmActions:
        - !Ref AlarmTopic

  # Additional alarms for memory, response time, error rates, etc.
  # ...

  AlarmTopic:
    Type: AWS::SNS::Topic
    Properties:
      DisplayName: !Sub ${AWS::StackName}-Alarms
      TopicName: !Sub ${AWS::StackName}-Alarms

Parameters:
  ECSServiceName:
    Type: String
    Description: 'Name of the ECS Service'
  
  ECSClusterName:
    Type: String
    Description: 'Name of the ECS Cluster'
  
  DBInstanceIdentifier:
    Type: String
    Description: 'RDS Instance Identifier'
  
  LoadBalancerName:
    Type: String
    Description: 'Load Balancer Name'
```

### 2. Application Logging

```python
# app/core/logging.py
import logging
import json
import os
from datetime import datetime
from pythonjsonlogger import jsonlogger
from app.core.phi_sanitizer import sanitize_phi

class PHISafeJsonFormatter(jsonlogger.JsonFormatter):
    """
    JSON formatter that sanitizes potential PHI in log messages.
    """
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp with ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add trace ID for correlation if available
        trace_id = getattr(record, 'trace_id', None)
        if trace_id:
            log_record['trace_id'] = trace_id
        
        # Add AWS request ID if running in Lambda/API Gateway
        aws_request_id = os.environ.get('AWS_REQUEST_ID')
        if aws_request_id:
            log_record['aws_request_id'] = aws_request_id
        
        # Sanitize all string fields for potential PHI
        for key, value in log_record.items():
            if isinstance(value, str):
                log_record[key] = sanitize_phi(value)

def configure_logging():
    """Configure application logging with PHI protection."""
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Create JSON formatter
    formatter = PHISafeJsonFormatter(
        '%(timestamp)s %(levelname)s %(name)s %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Disable propagation for third-party loggers to prevent PHI leakage
    for logger_name in ['boto3', 'botocore', 'urllib3', 'sqlalchemy.engine']:
        logging.getLogger(logger_name).propagate = False
```

## Implementation Steps

1. **Infrastructure Setup**
   - Create VPC with public and private subnets
   - Set up security groups and network ACLs
   - Configure RDS with encryption and high availability
   - Set up ECS cluster and ECR repositories
   - Configure WAF and security settings

2. **CI/CD Pipeline Setup**
   - Create GitHub repository and configure webhooks
   - Set up CodePipeline with source, build, and deploy stages
   - Configure CodeBuild project with security scanning
   - Set up automated testing and deployment

3. **Application Containerization**
   - Create multi-stage Dockerfile
   - Configure container security settings
   - Set up Docker Compose for local development

4. **Monitoring and Alerting**
   - Set up CloudWatch dashboards and alarms
   - Configure log aggregation and analysis
   - Set up automated incident response

5. **Disaster Recovery and Backup**
   - Configure cross-region replication
   - Set up data backup schedules
   - Create disaster recovery runbooks and testing

## HIPAA Compliance Validation

- **Infrastructure Security Assessment**: Validate that all infrastructure components meet HIPAA security requirements
- **Automated Compliance Checking**: Implement continuous compliance validation in the CI/CD pipeline
- **Penetration Testing**: Conduct regular penetration testing on the deployment environment
- **Disaster Recovery Testing**: Perform periodic disaster recovery exercises to validate recovery procedures
- **Access Control Audit**: Regularly audit access controls and permissions across all components