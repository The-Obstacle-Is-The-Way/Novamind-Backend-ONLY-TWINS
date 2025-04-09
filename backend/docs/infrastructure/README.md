# Novamind Digital Twin: Infrastructure Documentation

This directory contains documentation related to the infrastructure and deployment architecture of the Novamind Digital Twin platform.

## Infrastructure Documentation

| Document | Description |
|----------|-------------|
| [AWS_INFRASTRUCTURE.md](./AWS_INFRASTRUCTURE.md) | Detailed guide for AWS-based infrastructure implementation |

## Related Documentation

For additional deployment information, refer to:

- [DEPLOYMENT.md](../DEPLOYMENT.md) - General deployment guidelines
- [README-PRODUCTION.md](../README-PRODUCTION.md) - Production deployment instructions

## Infrastructure Architecture

The Novamind Digital Twin platform uses a cloud-native architecture on AWS with the following key components:

1. **Compute**: Serverless Lambda functions and containerized ECS/EKS services
2. **Storage**: S3, DynamoDB, and Aurora PostgreSQL for different data types
3. **Security**: IAM, KMS, and AWS Secrets Manager for HIPAA compliance
4. **Networking**: API Gateway, VPC, and AWS Transit Gateway
5. **Monitoring**: CloudWatch, X-Ray, and custom logging solutions