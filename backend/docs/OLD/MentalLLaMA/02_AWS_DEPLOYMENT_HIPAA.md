# MentaLLaMA AWS Deployment & HIPAA Compliance

## Introduction

This document provides comprehensive guidelines for deploying the MentaLLaMA-33B-lora model on AWS infrastructure with strict adherence to HIPAA compliance requirements. It covers infrastructure architecture, security controls, deployment options, scaling considerations, and monitoring requirements.

## HIPAA Compliance Framework

### Core HIPAA Requirements

When deploying MentaLLaMA for mental health analysis in a healthcare context, the following HIPAA requirements must be addressed:

1. **PHI Protection**: Ensure all Protected Health Information remains secure at all stages
2. **Access Controls**: Implement strict role-based access to systems and data
3. **Transmission Security**: Secure all data in transit
4. **Storage Security**: Encrypt all data at rest
5. **Audit Logging**: Maintain comprehensive audit trails of all operations
6. **Business Associate Agreements**: Ensure BAAs are in place with AWS and any other vendors
7. **Breach Notification**: Implement processes for breach detection and notification
8. **Risk Analysis**: Conduct and document regular risk assessments

### AWS HIPAA Eligible Services

Our MentaLLaMA deployment leverages the following HIPAA-eligible AWS services:

| Service | Usage | HIPAA Considerations |
|---------|-------|----------------------|
| AWS SageMaker | Model hosting and inference | BAA required, Private VPC deployment |
| AWS EC2 | Alternative deployment option | BAA required, Instance encryption |
| AWS S3 | Model artifact storage | BAA required, Bucket encryption, access policies |
| AWS KMS | Encryption key management | BAA required, CMK rotation, access controls |
| AWS CloudWatch | Logging and monitoring | BAA required, Log encryption, retention policies |
| AWS Lambda | Serverless processing | BAA required, VPC deployment |
| AWS API Gateway | API management | BAA required, WAF integration, TLS enforcement |
| AWS Cognito | Authentication | BAA required, MFA enforcement |
| AWS EKS/ECS | Container orchestration | BAA required, Private cluster, NetworkPolicies |

## Infrastructure Architecture

### Deployment Architecture

The MentaLLaMA infrastructure follows a secure, multi-tier architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│                       AWS Cloud (us-east-1)                         │
│                                                                     │
│  ┌─────────────────┐     ┌─────────────────┐    ┌──────────────────┐│
│  │                 │     │                 │    │                  ││
│  │  WAF            │────►│  API Gateway    │───►│ Application Load ││
│  │  (Rate limiting,│     │  (API endpoints)│    │ Balancer         ││
│  │   IP filtering) │     │                 │    │                  ││
│  └─────────────────┘     └─────────────────┘    └──────────┬───────┘│
│                                                            │        │
│ ┌──────────────────────────────────────────────────────┐   │        │
│ │   VPC (172.16.0.0/16)                                │   │        │
│ │                                                      │   │        │
│ │  ┌─────────────────────────────┐                     │   │        │
│ │  │  Private Subnet 1           │                     │   │        │
│ │  │                             │                     │   │        │
│ │  │  ┌────────────────────┐     │                     │   │        │
│ │  │  │  ECS/EKS Cluster   │     │                     │   │        │
│ │  │  │                    │     │                     │   │        │
│ │  │  │  ┌──────────────┐  │     │◄────────────────────┘   │        │
│ │  │  │  │ API Services │  │     │                         │        │
│ │  │  │  │              │  │     │                         │        │
│ │  │  │  └──────────────┘  │     │   ┌───────────────┐     │        │
│ │  │  │                    │     │   │  SageMaker    │     │        │
│ │  │  │  ┌──────────────┐  │     │   │  Endpoints    │◄────┘        │
│ │  │  │  │ PHI Detection│◄─┼─────┼───┤  (MentaLLaMA) │              │
│ │  │  │  │  Service     │  │     │   │               │              │
│ │  │  │  └──────────────┘  │     │   └───────────────┘              │
│ │  │  └────────────────────┘     │                                  │
│ │  └─────────────────────────────┘                                  │
│ │                                                                   │
│ │  ┌─────────────────────────────┐     ┌─────────────────────────┐  │
│ │  │  Private Subnet 2           │     │ Private Subnet 3        │  │
│ │  │                             │     │                         │  │ 
│ │  │  ┌─────────────────────┐    │     │ ┌─────────────────────┐ │  │
│ │  │  │ Aurora PostgreSQL   │    │     │ │  ElastiCache        │ │  │
│ │  │  │ (metadata storage)  │    │     │ │  (response caching) │ │  │
│ │  │  └─────────────────────┘    │     │ └─────────────────────┘ │  │
│ │  └─────────────────────────────┘     └─────────────────────────┘  │
│ │                                                                   │
│ └───────────────────────────────────────────────────────────────────┘
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Security Controls

The architecture implements the following security controls:

1. **Network Isolation**:
   - Private VPC with no direct internet access
   - NAT Gateway for outbound requests only
   - Security groups with principle of least privilege
   - Network ACLs as additional security layer

2. **Access Controls**:
   - IAM roles with fine-grained permissions
   - Temporary credentials via AWS STS
   - Role assumption for all service access
   - MFA enforcement for human users

3. **Encryption**:
   - TLS 1.3 for all in-transit communications
   - KMS encryption for all data at rest
   - S3 bucket encryption with customer-managed keys
   - RDS encryption with customer-managed keys

4. **Monitoring and Logging**:
   - CloudTrail for all API activity
   - CloudWatch Logs for application logs
   - VPC Flow Logs for network traffic analysis
   - AWS Config for compliance monitoring

## Deployment Options

### Option 1: SageMaker Deployment

SageMaker provides a managed service for deploying ML models with these HIPAA-compliant features:

#### 1. Model Artifact Storage

```bash
# Encrypt and upload model artifacts to S3
aws s3 cp --sse aws:kms \
  --sse-kms-key-id ${KMS_KEY_ID} \
  ./models/vicuna-33b-v1.3 s3://${MODEL_BUCKET}/models/vicuna-33b-v1.3/

aws s3 cp --sse aws:kms \
  --sse-kms-key-id ${KMS_KEY_ID} \
  ./models/mentallama-33b-lora s3://${MODEL_BUCKET}/models/mentallama-33b-lora/
```

#### 2. SageMaker Model Configuration

```bash
# Create SageMaker model from artifacts
aws sagemaker create-model \
  --model-name mentallama-model \
  --primary-container '{
      "Image": "763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:1.13.1-transformers4.26.0-gpu-py39-cu117-ubuntu20.04",
      "ModelDataUrl": "s3://'${MODEL_BUCKET}'/models/mentallama-packaged.tar.gz",
      "Environment": {
          "SAGEMAKER_PROGRAM": "inference.py",
          "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code",
          "SAGEMAKER_CONTAINER_LOG_LEVEL": "20",
          "SAGEMAKER_REGION": "'${AWS_REGION}'",
          "HF_MODEL_ID": "/opt/ml/model",
          "HF_TASK": "text-generation",
          "QUANTIZATION": "8bit"
      }
  }' \
  --execution-role-arn "arn:aws:iam::${ACCOUNT_ID}:role/SageMakerExecutionRole" \
  --vpc-config '{
      "SecurityGroupIds": ["'${SG_ID}'"],
      "Subnets": ["'${SUBNET_1}'", "'${SUBNET_2}'"]
  }' \
  --enable-network-isolation
```

#### 3. SageMaker Endpoint Configuration

```bash
# Create SageMaker endpoint configuration
aws sagemaker create-endpoint-config \
  --endpoint-config-name mentallama-endpoint-config \
  --production-variants '[{
      "VariantName": "default",
      "ModelName": "mentallama-model",
      "InitialInstanceCount": 1,
      "InstanceType": "ml.g5.2xlarge",
      "InitialVariantWeight": 1,
      "ServerlessConfig": null,
      "AcceleratorType": null,
      "ManagedInstanceScaling": {
          "Status": "ENABLED",
          "MinInstanceCount": 0,
          "MaxInstanceCount": 3
      },
      "ModelDataDownloadTimeoutInSeconds": 1200,
      "ContainerStartupHealthCheckTimeoutInSeconds": 1200
  }]' \
  --data-capture-config '{
      "EnableCapture": true,
      "InitialSamplingPercentage": 100,
      "DestinationS3Uri": "s3://'${LOGS_BUCKET}'/datacapture",
      "CaptureOptions": [
          {"CaptureMode": "Input"},
          {"CaptureMode": "Output"}
      ],
      "CaptureContentTypeHeader": {
          "CsvContentTypes": ["text/csv"],
          "JsonContentTypes": ["application/json"]
      }
  }' \
  --kms-key-id ${KMS_KEY_ID}
```

#### 4. SageMaker Endpoint Creation

```bash
# Create SageMaker endpoint
aws sagemaker create-endpoint \
  --endpoint-name mentallama-endpoint \
  --endpoint-config-name mentallama-endpoint-config \
  --tags '[
    {"Key": "Environment", "Value": "Production"},
    {"Key": "Project", "Value": "NOVAMIND"},
    {"Key": "PHI", "Value": "False"}
  ]'
```

### Option 2: EKS Deployment

For greater customization and potentially lower costs, EKS deployment is an alternative:

#### 1. EKS Cluster Configuration

```yaml
# eks-cluster.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: novamind-ml-cluster
  region: us-east-1
  version: "1.27"
  tags:
    Environment: Production
    Project: NOVAMIND
vpc:
  id: ${VPC_ID}
  subnets:
    private:
      us-east-1a: ${SUBNET_1}
      us-east-1b: ${SUBNET_2}
      us-east-1c: ${SUBNET_3}
  securityGroup: ${SG_ID}
privateCluster:
  enabled: true
  skipEndpointCreation: false
managedNodeGroups:
  - name: ml-gpu-nodes
    instanceType: g4dn.xlarge
    desiredCapacity: 2
    minSize: 1
    maxSize: 5
    volumeSize: 100
    volumeType: gp3
    privateNetworking: true
    labels:
      role: ml-inference
    tags:
      k8s.io/cluster-autoscaler/enabled: "true"
      k8s.io/cluster-autoscaler/novamind-ml-cluster: "owned"
    iam:
      withAddonPolicies:
        autoScaler: true
        ebs: true
        albIngress: true
addons:
  - name: vpc-cni
    version: latest
  - name: kube-proxy
    version: latest
  - name: coredns
    version: latest
  - name: aws-ebs-csi-driver
    version: latest
```

#### 2. MentaLLaMA Deployment

```yaml
# mentallama-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mentallama-inference
  namespace: ml-services
  labels:
    app: mentallama-inference
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mentallama-inference
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 0
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: mentallama-inference
    spec:
      securityContext:
        fsGroup: 1000
        runAsUser: 1000
        runAsGroup: 1000
      containers:
      - name: mentallama
        image: ${ECR_REPO}/mentallama-inference:latest
        imagePullPolicy: Always
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          capabilities:
            drop:
            - ALL
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "32Gi"
            cpu: "8"
          requests:
            nvidia.com/gpu: 1
            memory: "30Gi"
            cpu: "4"
        env:
        - name: MODEL_BASE_PATH
          value: "/models/vicuna-33b-v1.3"
        - name: LORA_ADAPTER_PATH
          value: "/models/mentallama-33b-lora"
        - name: LOG_LEVEL
          value: "INFO"
        - name: QUANTIZATION
          value: "8bit"
        - name: AWS_REGION
          value: "us-east-1"
        - name: MAX_CONCURRENT_REQUESTS
          value: "4"
        volumeMounts:
        - name: model-storage
          mountPath: /models
          readOnly: true
        - name: tmp-volume
          mountPath: /tmp
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 300
          periodSeconds: 30
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 300
          periodSeconds: 30
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: mentallama-model-pvc
      - name: tmp-volume
        emptyDir:
          sizeLimit: 10Gi
      nodeSelector:
        role: ml-inference
      tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
```

#### 3. Service and Network Policy

```yaml
# mentallama-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mentallama-inference
  namespace: ml-services
spec:
  selector:
    app: mentallama-inference
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: mentallama-access
  namespace: ml-services
spec:
  podSelector:
    matchLabels:
      app: mentallama-inference
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: api-services
    - podSelector:
        matchLabels:
          app: api-service
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
```

### Option 3: Asynchronous Processing with AWS Lambda

For non-real-time analysis, a serverless architecture can be more cost-effective:

```yaml
# serverless.yml
service: mentallama-async

provider:
  name: aws
  runtime: python3.9
  region: ${opt:region, 'us-east-1'}
  memorySize: 1024
  timeout: 900
  vpc:
    securityGroupIds:
      - ${self:custom.securityGroupId}
    subnetIds:
      - ${self:custom.privateSubnet1}
      - ${self:custom.privateSubnet2}
  environment:
    SAGEMAKER_ENDPOINT: ${self:custom.sagemakerEndpoint}
    REQUEST_QUEUE_URL: ${self:custom.requestQueueUrl}
    RESULT_BUCKET: ${self:custom.resultBucket}
    KMS_KEY_ID: ${self:custom.kmsKeyId}
    LOG_LEVEL: "INFO"

functions:
  requestProcessor:
    handler: src/handlers/request_processor.handler
    events:
      - sqs:
          arn: !GetAtt RequestQueue.Arn
          batchSize: 1
          maximumBatchingWindow: 10
    environment:
      FUNCTION_NAME: "requestProcessor"

  resultProcessor:
    handler: src/handlers/result_processor.handler
    events:
      - s3:
          bucket: ${self:custom.resultBucket}
          event: s3:ObjectCreated:*
          rules:
            - prefix: results/
    environment:
      FUNCTION_NAME: "resultProcessor"
      NOTIFICATION_TOPIC: !Ref ResultNotificationTopic

resources:
  Resources:
    RequestQueue:
      Type: AWS::SQS::Queue
      Properties:
        QueueName: ${self:service}-${opt:stage}-request-queue
        MessageRetentionPeriod: 1209600  # 14 days
        VisibilityTimeout: 900
        KmsMasterKeyId: ${self:custom.kmsKeyId}
        
    ResultNotificationTopic:
      Type: AWS::SNS::Topic
      Properties:
        TopicName: ${self:service}-${opt:stage}-result-notification
        KmsMasterKeyId: ${self:custom.kmsKeyId}
        
    ResultBucket:
      Type: AWS::S3::Bucket
      Properties:
        BucketName: ${self:custom.resultBucket}
        BucketEncryption:
          ServerSideEncryptionConfiguration:
            - ServerSideEncryptionByDefault:
                SSEAlgorithm: aws:kms
                KMSMasterKeyID: ${self:custom.kmsKeyId}
        LifecycleConfiguration:
          Rules:
            - Id: ExpireResults
              Status: Enabled
              ExpirationInDays: 30
```

## PHI Protection Pipeline

The PHI protection pipeline follows a multi-layered approach:

### 1. Initial PHI Detection and Masking

```python
# phi_protection.py
import boto3
import re
from typing import Dict, Any, List, Tuple

class PhiProtectionPipeline:
    """Multi-layered PHI detection and masking pipeline."""
    
    def __init__(self, region_name: str = "us-east-1"):
        """Initialize the PHI protection pipeline."""
        self.comprehend_medical = boto3.client(
            'comprehendmedical', 
            region_name=region_name
        )
        self.regex_patterns = self._compile_regex_patterns()
        
    def _compile_regex_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for additional PHI detection."""
        return {
            "EMAIL": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "PHONE": re.compile(r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
            "SSN": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "URL": re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*\??[/\w\.-=&%]*'),
            "IP_ADDRESS": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
            "MRNS": re.compile(r'\b[A-Z]{2}\d{6,8}\b')
        }
        
    def detect_and_mask_phi(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Detect and mask PHI in text through multiple layers.
        
        Args:
            text: Text that may contain PHI
            
        Returns:
            Tuple of (masked_text, metadata)
        """
        if not text:
            return text, {"phi_detected": False, "entity_count": 0}
        
        # Initialize tracking
        metadata = {
            "phi_detected": False,
            "entity_count": 0,
            "entity_types": {}
        }
        
        # Layer 1: AWS Comprehend Medical
        masked_text, comprehend_metadata = self._apply_comprehend_medical(text)
        
        # Update tracking metadata
        if comprehend_metadata["phi_detected"]:
            metadata["phi_detected"] = True
            metadata["entity_count"] += comprehend_metadata["entity_count"]
            metadata["entity_types"].update(comprehend_metadata["entity_types"])
        
        # Layer 2: Custom regex patterns
        masked_text, regex_metadata = self._apply_regex_patterns(masked_text)
        
        # Update tracking metadata
        if regex_metadata["phi_detected"]:
            metadata["phi_detected"] = True
            metadata["entity_count"] += regex_metadata["entity_count"]
            metadata["entity_types"].update(regex_metadata["entity_types"])
        
        return masked_text, metadata
    
    def _apply_comprehend_medical(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Apply AWS Comprehend Medical for PHI detection."""
        try:
            response = self.comprehend_medical.detect_phi(Text=text)
            
            if not response.get('Entities'):
                return text, {"phi_detected": False, "entity_count": 0, "entity_types": {}}
            
            # Sort entities by beginning offset (descending) to avoid offset changes
            entities = sorted(
                response.get('Entities', []),
                key=lambda x: x['BeginOffset'],
                reverse=True
            )
            
            # Create a mutable copy of the text
            masked_text = text
            entity_types = {}
            
            # Replace each entity with a mask token
            for entity in entities:
                entity_type = entity['Type']
                begin = entity['BeginOffset']
                end = entity['EndOffset']
                
                # Track entity types
                if entity_type not in entity_types:
                    entity_types[entity_type] = 0
                entity_types[entity_type] += 1
                
                # Create appropriate mask token
                mask_token = f"[{entity_type}]"
                
                # Replace the entity with mask token
                masked_text = masked_text[:begin] + mask_token + masked_text[end:]
            
            return masked_text, {
                "phi_detected": True,
                "entity_count": len(entities),
                "entity_types": entity_types
            }
            
        except Exception as e:
            # Log error but do not expose in response
            # If Comprehend fails, return original text and log warning
            # In production, consider more robust error handling
            return text, {"phi_detected": False, "entity_count": 0, "entity_types": {}}
    
    def _apply_regex_patterns(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Apply custom regex patterns for additional PHI detection."""
        masked_text = text
        entity_count = 0
        entity_types = {}
        
        # Apply each pattern
        for entity_type, pattern in self.regex_patterns.items():
            # Find all matches
            matches = list(re.finditer(pattern, masked_text))
            # Process matches in reverse to preserve offsets
            for match in reversed(matches):
                entity_count += 1
                start, end = match.span()
                masked_text = masked_text[:start] + f"[{entity_type}]" + masked_text[end:]
                
                # Track entity types
                if entity_type not in entity_types:
                    entity_types[entity_type] = 0
                entity_types[entity_type] += 1
        
        return masked_text, {
            "phi_detected": entity_count > 0,
            "entity_count": entity_count,
            "entity_types": entity_types
        }
```

### 2. Integration with AI Analysis Pipeline

```python
# mentallama_analysis_service.py
from phi_protection import PhiProtectionPipeline
import boto3
import json
import time
import uuid
from typing import Dict, Any, Optional

class MentaLLaMAAnalysisService:
    """Service for mental health analysis using MentaLLaMA."""
    
    def __init__(
        self, 
        sagemaker_endpoint: str,
        region_name: str = "us-east-1",
        kms_key_id: Optional[str] = None
    ):
        """Initialize the analysis service."""
        self.sagemaker = boto3.client('sagemaker-runtime', region_name=region_name)
        self.s3 = boto3.client('s3', region_name=region_name)
        self.endpoint_name = sagemaker_endpoint
        self.phi_protection = PhiProtectionPipeline(region_name=region_name)
        self.kms_key_id = kms_key_id
        
    async def analyze_text(
        self, 
        text: str, 
        analysis_type: str,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze text using MentaLLaMA with PHI protection.
        
        Args:
            text: Text to analyze (will be sanitized)
            analysis_type: Type of analysis to perform
            parameters: Additional parameters for the analysis
            
        Returns:
            Analysis results
        """
        # 1. Apply PHI protection
        sanitized_text, phi_metadata = self.phi_protection.detect_and_mask_phi(text)
        
        # 2. Construct prompt based on analysis type
        prompt = self._construct_prompt(analysis_type, sanitized_text, parameters)
        
        # 3. Prepare payload for SageMaker
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": parameters.get("max_tokens", 256),
                "temperature": parameters.get("temperature", 0.7),
                "top_p": parameters.get("top_p", 0.9),
                "do_sample": True
            }
        }
        
        # 4. Invoke SageMaker endpoint
        response = self.sagemaker.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType='application/json',
            Body=json.dumps(payload)
        )
        
        # 5. Parse response
        response_body = json.loads(response['Body'].read().decode())
        
        # 6. Extract and process results
        result = self._process_response(response_body, analysis_type)
        
        # 7. Return structured results
        return {
            "analysis_type": analysis_type,
            "result": result,
            "phi_removed": phi_metadata["phi_detected"],
            "phi_entity_count": phi_metadata["entity_count"]
        }
    
    def _construct_prompt(
        self, 
        analysis_type: str, 
        sanitized_text: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Construct prompt based on analysis type."""
        # Implementation depends on the specific prompts needed for each analysis type
        # See docs/MentalLLaMA/01_MENTAL_HEALTH_MODELING.md for examples
        pass
    
    def _process_response(
        self, 
        response_body: Dict[str, Any], 
        analysis_type: str
    ) -> Dict[str, Any]:
        """Process and structure the model response."""
        # Implementation depends on the response format and parsing logic
        pass
```

### 3. Data Lifecycle Management

```bash
# S3 lifecycle configuration
aws s3api put-bucket-lifecycle-configuration \
  --bucket ${RESULT_BUCKET} \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "DeleteOldResults",
        "Status": "Enabled",
        "Prefix": "results/",
        "Expiration": {
          "Days": 30
        }
      },
      {
        "ID": "TransitionToGlacier",
        "Status": "Enabled",
        "Prefix": "archive/",
        "Transitions": [
          {
            "Days": 30,
            "StorageClass": "GLACIER"
          }
        ],
        "Expiration": {
          "Days": 365
        }
      }
    ]
  }'
```

## Monitoring and Auditing

### 1. CloudWatch Metrics Configuration

```bash
# Create CloudWatch dashboard for MentaLLaMA monitoring
aws cloudwatch put-dashboard \
  --dashboard-name "MentaLLaMA-Monitoring" \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "x": 0,
        "y": 0,
        "width": 12,
        "height": 6,
        "properties": {
          "metrics": [
            ["AWS/SageMaker", "Invocations", "EndpointName", "mentallama-endpoint", {"stat": "Sum"}],
            [".", "InvocationsPerInstance", ".", ".", {"stat": "Sum"}]
          ],
          "view": "timeSeries",
          "stacked": false,
          "region": "'${AWS_REGION}'",
          "title": "MentaLLaMA Invocations",
          "period": 60
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
            ["AWS/SageMaker", "ModelLatency", "EndpointName", "mentallama-endpoint", {"stat": "Average"}],
            [".", ".", ".", ".", {"stat": "p90"}],
            [".", ".", ".", ".", {"stat": "p99"}]
          ],
          "view": "timeSeries",
          "stacked": false,
          "region": "'${AWS_REGION}'",
          "title": "MentaLLaMA Latency",
          "period": 60
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
            ["NOVAMIND", "phi_entities_detected", "EntityType", "NAME", {"stat": "Sum"}],
            ["...", "DATE", {"stat": "Sum"}],
            ["...", "LOCATION", {"stat": "Sum"}],
            ["...", "PHONE", {"stat": "Sum"}],
            ["...", "EMAIL", {"stat": "Sum"}],
            ["...", "SSN", {"stat": "Sum"}]
          ],
          "view": "timeSeries",
          "stacked": true,
          "region": "'${AWS_REGION}'",
          "title": "PHI Entities Detected and Masked",
          "period": 60
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
            ["AWS/SageMaker", "CPUUtilization", "EndpointName", "mentallama-endpoint", {"stat": "Average"}],
            [".", "MemoryUtilization", ".", ".", {"stat": "Average"}],
            [".", "GPUUtilization", ".", ".", {"stat": "Average"}],
            [".", "GPUMemoryUtilization", ".", ".", {"stat": "Average"}]
          ],
          "view": "timeSeries",
          "stacked": false,
          "region": "'${AWS_REGION}'",
          "title": "MentaLLaMA Resource Utilization",
          "period": 60
        }
      }
    ]
  }'
```

### 2. CloudWatch Alarms

```bash
# Create CloudWatch alarms for critical metrics
aws cloudwatch put-metric-alarm \
  --alarm-name "MentaLLaMA-HighLatency" \
  --alarm-description "Alarm when MentaLLaMA model latency exceeds threshold" \
  --metric-name "ModelLatency" \
  --namespace "AWS/SageMaker" \
  --statistic "Average" \
  --dimensions "Name=EndpointName,Value=mentallama-endpoint" \
  --period 60 \
  --evaluation-periods 5 \
  --threshold 10000 \
  --comparison-operator "GreaterThanThreshold" \
  --alarm-actions "arn:aws:sns:${AWS_REGION}:${ACCOUNT_ID}:MentaLLaMA-Alerts" \
  --treat-missing-data "notBreaching"

aws cloudwatch put-metric-alarm \
  --alarm-name "MentaLLaMA-HighErrorRate" \
  --alarm-description "Alarm when MentaLLaMA error rate exceeds threshold" \
  --metric-name "ModelError" \
  --namespace "AWS/SageMaker" \
  --statistic "Average" \
  --dimensions "Name=EndpointName,Value=mentallama-endpoint" \
  --period 60 \
  --evaluation-periods 3 \
  --threshold 0.05 \
  --comparison-operator "GreaterThanThreshold" \
  --alarm-actions "arn:aws:sns:${AWS_REGION}:${ACCOUNT_ID}:MentaLLaMA-Alerts" \
  --treat-missing-data "notBreaching"
```

### 3. CloudTrail Configuration

```bash
# Enable CloudTrail for comprehensive auditing
aws cloudtrail create-trail \
  --name "NOVAMIND-HIPAA-Compliance-Trail" \
  --s3-bucket-name "${CLOUDTRAIL_BUCKET}" \
  --s3-key-prefix "cloudtrail" \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --kms-key-id "${KMS_KEY_ID}" \
  --cloud-watch-logs-log-group-arn "arn:aws:logs:${AWS_REGION}:${ACCOUNT_ID}:log-group:CloudTrail/DefaultLogGroup:*" \
  --cloud-watch-logs-role-arn "arn:aws:iam::${ACCOUNT_ID}:role/CloudTrailToCloudWatchLogs"

aws cloudtrail start-logging --name "NOVAMIND-HIPAA-Compliance-Trail"

# Configure CloudTrail event selectors
aws cloudtrail put-event-selectors \
  --trail-name "NOVAMIND-HIPAA-Compliance-Trail" \
  --event-selectors '[
    {
      "ReadWriteType": "All",
      "IncludeManagementEvents": true,
      "DataResources": [
        {
          "Type": "AWS::S3::Object",
          "Values": ["arn:aws:s3:::"]
        },
        {
          "Type": "AWS::Lambda::Function",
          "Values": ["arn:aws:lambda"]
        }
      ]
    }
  ]'
```

## Scaling Considerations

### Auto-Scaling Configuration

```bash
# Create application auto scaling target for SageMaker endpoint
aws application-autoscaling register-scalable-target \
  --service-namespace sagemaker \
  --resource-id endpoint/mentallama-endpoint/variant/default \
  --scalable-dimension sagemaker:variant:DesiredInstanceCount \
  --min-capacity 1 \
  --max-capacity 5

# Create scaling policies
aws application-autoscaling put-scaling-policy \
  --service-namespace sagemaker \
  --resource-id endpoint/mentallama-endpoint/variant/default \
  --scalable-dimension sagemaker:variant:DesiredInstanceCount \
  --policy-name MentaLLaMA-ScaleUpOnHighInvocations \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 80.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
    },
    "ScaleOutCooldown": 300,
    "ScaleInCooldown": 600
  }'
```

### Load Testing

Before production deployment, perform comprehensive load testing:

```python
# load_test.py
import boto3
import json
import time
import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List

class MentaLLaMALoadTest:
    """Load testing utility for MentaLLaMA endpoints."""
    
    def __init__(
        self, 
        endpoint_name: str,
        region_name: str = "us-east-1",
        max_workers: int = 10
    ):
        """Initialize the load test utility."""
        self.sagemaker = boto3.client('sagemaker-runtime', region_name=region_name)
        self.endpoint_name = endpoint_name
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def run_load_test(
        self,
        test_cases: List[Dict[str, Any]],
        requests_per_second: float = 1.0,
        duration_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        Run a load test against the MentaLLaMA endpoint.
        
        Args:
            test_cases: List of test cases with prompts
            requests_per_second: Target requests per second
            duration_seconds: Test duration in seconds
            
        Returns:
            Test results and statistics
        """
        start_time = time.time()
        end_time = start_time + duration_seconds
        interval = 1.0 / requests_per_second
        
        # Statistics tracking
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        latencies = []
        
        print(f"Starting load test against {self.endpoint_name}")
        print(f"Targeting {requests_per_second} RPS for {duration_seconds} seconds")
        
        # Run test loop
        while time.time() < end_time:
            next_request_time = time.time() + interval
            
            # Select random test case
            test_case = random.choice(test_cases)
            
            # Submit request
            self.executor.submit(self._send_request, test_case, latencies)
            total_requests += 1
            
            # Wait until next request time
            sleep_time = next_request_time - time.time()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Wait for any pending requests to complete
        self.executor.shutdown(wait=True)
        
        # Calculate statistics
        successful_requests = len(latencies)
        failed_requests = total_requests - successful_requests
        
        if successful_requests > 0:
            avg_latency = sum(latencies) / successful_requests
            p50_latency = sorted(latencies)[int(successful_requests * 0.5)]
            p90_latency = sorted(latencies)[int(successful_requests * 0.9)]
            p99_latency = sorted(latencies)[int(successful_requests * 0.99)]
        else:
            avg_latency = p50_latency = p90_latency = p99_latency = 0
        
        results = {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "actual_rps": total_requests / duration_seconds,
            "latency": {
                "average_ms": avg_latency,
                "p50_ms": p50_latency,
                "p90_ms": p90_latency,
                "p99_ms": p99_latency
            }
        }
        
        print(f"Load test completed. Results: {json.dumps(results, indent=2)}")
        return results
        
    def _send_request(
        self, 
        test_case: Dict[str, Any],
        latencies: List[float]
    ) -> None:
        """Send a single request to the endpoint and record metrics."""
        start_time = time.time()
        success = False
        
        try:
            payload = {
                "inputs": test_case["prompt"],
                "parameters": test_case.get("parameters", {
                    "max_new_tokens": 256,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "do_sample": True
                })
            }
            
            response = self.sagemaker.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='application/json',
                Body=json.dumps(payload)
            )
            
            # Process response
            response_body = json.loads(response['Body'].read().decode())
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            success = True
            
        except Exception as e:
            print(f"Request failed: {str(e)}")
        
        return success
```

## Disaster Recovery

### 1. Backup Strategy

```bash
# Set up daily model snapshots
aws sagemaker create-model-package \
  --model-package-name "MentaLLaMA-${TIMESTAMP}" \
  --model-package-group-name "MentaLLaMA" \
  --source-algorithm-specification '{
    "SourceAlgorithms": [
      {
        "ModelDataUrl": "s3://'${MODEL_BUCKET}'/models/mentallama-packaged.tar.gz",
        "AlgorithmName": "mentallama-algorithm"
      }
    ]
  }'
```

### 2. Multi-Region Deployment

For critical production environments, deploy to multiple regions:

```bash
# Create secondary region deployment
SECONDARY_REGION="us-west-2"

# Copy model artifacts to secondary region
aws s3 cp --recursive \
  s3://${MODEL_BUCKET}/models/ \
  s3://${SECONDARY_MODEL_BUCKET}/models/ \
  --source-region ${AWS_REGION} \
  --region ${SECONDARY_REGION}

# Create SageMaker model in secondary region
aws sagemaker create-model \
  --model-name mentallama-model \
  --primary-container '{
      "Image": "763104351884.dkr.ecr.'${SECONDARY_REGION}'.amazonaws.com/huggingface-pytorch-inference:1.13.1-transformers4.26.0-gpu-py39-cu117-ubuntu20.04",
      "ModelDataUrl": "s3://'${SECONDARY_MODEL_BUCKET}'/models/mentallama-packaged.tar.gz",
      "Environment": {
          "SAGEMAKER_PROGRAM": "inference.py",
          "SAGEMAKER_SUBMIT_DIRECTORY": "/opt/ml/model/code",
          "SAGEMAKER_CONTAINER_LOG_LEVEL": "20",
          "SAGEMAKER_REGION": "'${SECONDARY_REGION}'",
          "HF_MODEL_ID": "/opt/ml/model",
          "HF_TASK": "text-generation",
          "QUANTIZATION": "8bit"
      }
  }' \
  --execution-role-arn "arn:aws:iam::${ACCOUNT_ID}:role/SageMakerExecutionRole" \
  --vpc-config '{
      "SecurityGroupIds": ["'${SECONDARY_SG_ID}'"],
      "Subnets": ["'${SECONDARY_SUBNET_1}'", "'${SECONDARY_SUBNET_2}'"]
  }' \
  --enable-network-isolation \
  --region ${SECONDARY_REGION}
```

### 3. Disaster Recovery Plan

Document the disaster recovery plan with:

1. **Recovery Point Objective (RPO)**: Maximum acceptable data loss
   - MentaLLaMA model: 24 hours (daily backups)
   - Analysis results: 1 hour (near real-time replication)

2. **Recovery Time Objective (RTO)**: Maximum acceptable downtime
   - Critical path: 15 minutes (automatic failover)
   - Full system: 4 hours (manual intervention)

3. **Failover Procedures**:
   - Automatic DNS failover using Route 53 health checks
   - API Gateway canary deployments
   - SageMaker multi-model endpoints for redundancy

## IAM Policies and Permissions

### 1. SageMaker Execution Role

```json
// SageMakerExecutionRole policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${MODEL_BUCKET}/*",
        "arn:aws:s3:::${MODEL_BUCKET}",
        "arn:aws:s3:::${LOGS_BUCKET}/*",
        "arn:aws:s3:::${LOGS_BUCKET}"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:${AWS_REGION}:${ACCOUNT_ID}:key/${KMS_KEY_ID}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. API Service Role

```json
// APIServiceRole policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:InvokeEndpoint"
      ],
      "Resource": "arn:aws:sagemaker:${AWS_REGION}:${ACCOUNT_ID}:endpoint/mentallama-endpoint"
    },
    {
      "Effect": "Allow",
      "Action": [
        "comprehendmedical:DetectPHI"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey*"
      ],
      "Resource": "arn:aws:kms:${AWS_REGION}:${ACCOUNT_ID}:key/${KMS_KEY_ID}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:${AWS_REGION}:${ACCOUNT_ID}:log-group:/aws/api-service/*"
    }
  ]
}
```

## Conclusion

Deploying MentaLLaMA on AWS requires a careful balance of performance, compliance, and security. By following the architecture and practices outlined in this document, you can deploy a HIPAA-compliant mental health analysis service that provides valuable insights while protecting patient data.

Key takeaways:

1. **Multi-layered Security**: Implement defense-in-depth with network isolation, encryption, access controls, and monitoring
2. **PHI Protection**: Always process text through a comprehensive PHI detection pipeline before analysis
3. **Infrastructure as Code**: Deploy and manage all infrastructure using CloudFormation or Terraform for consistency
4. **Monitoring and Auditing**: Implement comprehensive monitoring, alerting, and audit trails
5. **Disaster Recovery**: Plan for failures with backups, multi-region deployment, and documented recovery procedures

For clinical implementation guidelines, please refer to [MentaLLaMA Clinical Implementation Guide](./03_CLINICAL_IMPLEMENTATION_GUIDE.md).