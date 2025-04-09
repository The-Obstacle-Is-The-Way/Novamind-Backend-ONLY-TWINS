# TESTING_AND_DEPLOYMENT

## Overview

This document provides comprehensive guidelines for testing and deploying the NOVAMIND platform. All testing and deployment processes adhere to HIPAA compliance requirements and follow Clean Architecture principles to ensure a secure, reliable, and maintainable system.

## Testing Strategy

### Testing Pyramid

NOVAMIND implements a comprehensive testing strategy based on the testing pyramid:

```ascii
┌─────────────────────────────────────────────────────────────────────┐
│                         TESTING PYRAMID                             │
├─────────────────────────────────────────────────────────────────────┤
│                          ╱╲                                         │
│                         ╱  ╲                                        │
│                        ╱    ╲                                       │
│                       ╱ E2E  ╲                                      │
│                      ╱────────╲                                     │
│                     ╱          ╲                                    │
│                    ╱Integration ╲                                   │
│                   ╱──────────────╲                                  │
│                  ╱                ╲                                 │
│                 ╱   Unit Tests     ╲                                │
│                ╱────────────────────╲                               │
│               ╱                      ╲                              │
│              ╱────────────────────────╲                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

1. **Unit Tests**: Form the foundation of the testing strategy
2. **Integration Tests**: Verify interactions between components
3. **End-to-End Tests**: Validate complete user workflows

### Unit Testing

Unit tests focus on testing individual components in isolation, following these principles:

```python
# Example unit test for a domain service
import pytest
from unittest.mock import Mock, patch
from uuid import UUID

from app.domain.services.medication_service import MedicationService
from app.domain.entities.medication import Medication
from app.domain.exceptions import EntityNotFoundException

class TestMedicationService:
    """Unit tests for the MedicationService"""
    
    def setup_method(self):
        """Set up test dependencies with mocks"""
        self.medication_repository = Mock()
        self.patient_repository = Mock()
        self.audit_logger = Mock()
        
        self.service = MedicationService(
            medication_repository=self.medication_repository,
            patient_repository=self.patient_repository,
            audit_logger=self.audit_logger
        )
    
    def test_get_medication_by_id_returns_medication_when_exists(self):
        """Test that get_medication_by_id returns medication when it exists"""
        # Arrange
        medication_id = UUID("12345678-1234-5678-1234-567812345678")
        expected_medication = Medication(
            id=medication_id,
            name="Test Medication",
            dosage="10mg",
            frequency="Daily"
        )
        
        self.medication_repository.get_by_id.return_value = expected_medication
        
        # Act
        result = self.service.get_medication_by_id(medication_id)
        
        # Assert
        assert result == expected_medication
        self.medication_repository.get_by_id.assert_called_once_with(medication_id)
    
    def test_get_medication_by_id_raises_exception_when_not_exists(self):
        """Test that get_medication_by_id raises exception when medication doesn't exist"""
        # Arrange
        medication_id = UUID("12345678-1234-5678-1234-567812345678")
        self.medication_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(EntityNotFoundException):
            self.service.get_medication_by_id(medication_id)
        
        self.medication_repository.get_by_id.assert_called_once_with(medication_id)
```

#### Unit Testing Guidelines

1. **Test Domain Logic in Isolation**
   - Mock all external dependencies
   - Focus on business rules and logic
   - Ensure high coverage of domain layer (>90%)

2. **Test Data Access Logic**
   - Use in-memory databases for repository tests
   - Test all CRUD operations
   - Verify error handling and edge cases

3. **Test Application Services**
   - Mock domain services and repositories
   - Verify correct orchestration of dependencies
   - Test authorization and validation logic

### Integration Testing

Integration tests verify interactions between components:

```python
# Example integration test for repository and database
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.infrastructure.persistence.repositories.patient_repository import SQLAlchemyPatientRepository
from app.domain.entities.patient import Patient
from app.infrastructure.persistence.models.patient_model import PatientModel

class TestPatientRepository:
    """Integration tests for the SQLAlchemy Patient Repository"""
    
    @pytest.fixture
    async def db_session(self):
        """Create a test database session"""
        from app.infrastructure.persistence.database import get_test_db
        
        async for session in get_test_db():
            yield session
    
    @pytest.fixture
    def repository(self, db_session):
        """Create a repository instance with the test session"""
        return SQLAlchemyPatientRepository(db_session)
    
    async def test_create_and_get_patient(self, repository):
        """Test creating and retrieving a patient"""
        # Arrange
        patient = Patient(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            date_of_birth="1980-01-01"
        )
        
        # Act
        created_patient = await repository.create(patient)
        retrieved_patient = await repository.get_by_id(patient.id)
        
        # Assert
        assert retrieved_patient is not None
        assert retrieved_patient.id == patient.id
        assert retrieved_patient.first_name == patient.first_name
        assert retrieved_patient.last_name == patient.last_name
        assert retrieved_patient.email == patient.email
        assert retrieved_patient.date_of_birth == patient.date_of_birth
```

#### Integration Testing Guidelines

1. **Database Integration**
   - Test repository implementations with test databases
   - Verify ORM mappings and query performance
   - Test transactions and rollbacks

2. **External Service Integration**
   - Test API client implementations
   - Use mock servers for external services
   - Verify error handling and retry logic

3. **Middleware Integration**
   - Test authentication and authorization middleware
   - Verify request/response handling
   - Test error handling and logging

### End-to-End Testing

End-to-end tests validate complete user workflows:

```python
# Example end-to-end test using pytest and playwright
import pytest
from playwright.sync_api import Page, expect

class TestPatientDashboard:
    """End-to-end tests for the patient dashboard"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Set up the test by logging in"""
        # Navigate to login page
        page.goto("https://novamind.local/login")
        
        # Fill login form
        page.fill("input[name='email']", "test@example.com")
        page.fill("input[name='password']", "TestPassword123!")
        
        # Submit form
        page.click("button[type='submit']")
        
        # Wait for dashboard to load
        page.wait_for_selector(".dashboard-container")
    
    def test_view_medication_history(self, page: Page):
        """Test viewing medication history"""
        # Navigate to medications tab
        page.click("text=Medications")
        
        # Wait for medication list to load
        page.wait_for_selector(".medication-list")
        
        # Verify medication list is displayed
        expect(page.locator(".medication-item")).to_have_count(3)
        expect(page.locator(".medication-item").first).to_contain_text("Sertraline")
```

#### End-to-End Testing Guidelines

1. **Critical User Flows**
   - Test patient onboarding and registration
   - Test appointment scheduling and management
   - Test medication management and tracking
   - Test analytics dashboard functionality

2. **Security and Compliance**
   - Test authentication and authorization flows
   - Verify audit logging for sensitive operations
   - Test data encryption and privacy controls

3. **Performance and Reliability**
   - Test system performance under load
   - Verify system resilience to failures
   - Test backup and recovery procedures

### HIPAA-Compliant Testing

All testing must adhere to HIPAA compliance requirements:

1. **Test Data Management**
   - Use synthetic data for all tests
   - Never use real PHI in test environments
   - Implement data sanitization for test outputs

2. **Test Environment Security**
   - Secure access to test environments
   - Implement encryption for test databases
   - Regular security scanning of test environments

3. **Compliance Verification Tests**
   - Verify audit logging functionality
   - Test access controls and authorization
   - Validate data encryption and protection

## Continuous Integration and Deployment

### CI/CD Pipeline

NOVAMIND implements a comprehensive CI/CD pipeline for secure, reliable deployments:

```ascii
┌─────────────────────────────────────────────────────────────────────┐
│                         CI/CD PIPELINE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐        │
│  │         │     │         │     │         │     │         │        │
│  │  Code   │────▶│  Build  │────▶│  Test   │────▶│ Security│        │
│  │ Commit  │     │         │     │         │     │  Scan   │        │
│  │         │     │         │     │         │     │         │        │
│  └─────────┘     └─────────┘     └─────────┘     └────┬────┘        │
│                                                       │              │
│                                                       ▼              │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐        │
│  │         │     │         │     │         │     │         │        │
│  │ Release │◀────│ Deploy  │◀────│ Artifact│◀────│ Quality │        │
│  │         │     │         │     │ Publish │     │  Gate   │        │
│  │         │     │         │     │         │     │         │        │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### GitHub Actions Workflow

```yml
# .github/workflows/ci-cd.yml
name: NOVAMIND CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    name: Lint Code
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 black isort mypy
          pip install -r requirements-dev.txt
      - name: Lint with flake8
        run: flake8 app tests
      - name: Check formatting with black
        run: black --check app tests
      - name: Check imports with isort
        run: isort --check-only --profile black app tests
      - name: Type check with mypy
        run: mypy app

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/unit --cov=app --cov-report=xml
      - name: Run integration tests
        run: pytest tests/integration --cov=app --cov-report=xml --cov-append
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install bandit safety
      - name: Run bandit
        run: bandit -r app
      - name: Run safety
        run: safety check -r requirements.txt

  build:
    name: Build and Publish
    runs-on: ubuntu-latest
    needs: security-scan
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')
    steps:
      - uses: actions/checkout@v3
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      - name: Login to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ secrets.REGISTRY_URL }}
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ secrets.REGISTRY_URL }}/novamind/api:${{ github.sha }}
          cache-from: type=registry,ref=${{ secrets.REGISTRY_URL }}/novamind/api:latest
          cache-to: type=inline

  deploy-dev:
    name: Deploy to Development
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: development
    steps:
      - name: Deploy to Kubernetes
        uses: azure/k8s-deploy@v1
        with:
          namespace: novamind-dev
          manifests: |
            kubernetes/dev/deployment.yaml
            kubernetes/dev/service.yaml
          images: |
            ${{ secrets.REGISTRY_URL }}/novamind/api:${{ github.sha }}
          kubectl-version: 'latest'

  deploy-prod:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Deploy to Kubernetes
        uses: azure/k8s-deploy@v1
        with:
          namespace: novamind-prod
          manifests: |
            kubernetes/prod/deployment.yaml
            kubernetes/prod/service.yaml
          images: |
            ${{ secrets.REGISTRY_URL }}/novamind/api:${{ github.sha }}
          kubectl-version: 'latest'
```

### Deployment Environments

NOVAMIND uses multiple environments for progressive deployment:

1. **Development Environment**
   - Used for ongoing development and testing
   - Automatically deployed from the develop branch
   - Contains synthetic test data
   - Limited access for development team only

2. **Staging Environment**
   - Mirrors production configuration
   - Used for pre-release testing and validation
   - Contains anonymized data
   - Limited access for QA and development teams

3. **Production Environment**
   - Hosts live patient data
   - Deployed after thorough testing and approval
   - Strict access controls and monitoring
   - Regular security audits and compliance checks

### Deployment Architecture

NOVAMIND is deployed using a Kubernetes-based architecture:

```ascii
┌─────────────────────────────────────────────────────────────────────┐
│                      DEPLOYMENT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                     Kubernetes Cluster                       │    │
│  │                                                             │    │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │    │
│  │  │             │   │             │   │             │        │    │
│  │  │  API Pods   │   │   Worker    │   │  Frontend   │        │    │
│  │  │             │   │    Pods     │   │    Pods     │        │    │
│  │  └─────────────┘   └─────────────┘   └─────────────┘        │    │
│  │         │                 │                 │               │    │
│  │         ▼                 ▼                 ▼               │    │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │    │
│  │  │             │   │             │   │             │        │    │
│  │  │   Ingress   │   │  Services   │   │  ConfigMaps │        │    │
│  │  │             │   │             │   │  & Secrets  │        │    │
│  │  └─────────────┘   └─────────────┘   └─────────────┘        │    │
│  │                                                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────┐ │
│  │             │   │             │   │             │   │          │ │
│  │  Database   │   │    Redis    │   │ Object      │   │  Logging │ │
│  │  (RDS)      │   │  (ElastiCache) │ │ Storage    │   │  (CloudWatch) │
│  │             │   │             │   │ (S3)        │   │          │ │
│  └─────────────┘   └─────────────┘   └─────────────┘   └──────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Kubernetes Resources

```yml
# kubernetes/prod/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: novamind-api
  namespace: novamind-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: novamind-api
  template:
    metadata:
      labels:
        app: novamind-api
    spec:
      containers:
      - name: api
        image: ${REGISTRY_URL}/novamind/api:${IMAGE_TAG}
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: novamind-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: novamind-secrets
              key: jwt-secret
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: novamind-secrets
              key: aws-access-key
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom:
            secretKeyRef:
              name: novamind-secrets
              key: aws-secret-key
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      imagePullSecrets:
      - name: registry-credentials
```

## Monitoring and Observability

### Monitoring Stack

NOVAMIND uses a comprehensive monitoring stack:

1. **Metrics Collection**
   - Prometheus for metrics collection
   - Grafana for visualization
   - Custom dashboards for system health

2. **Logging**
   - Centralized logging with ELK stack
   - Structured logging format
   - HIPAA-compliant log filtering

3. **Tracing**
   - Distributed tracing with Jaeger
   - Request correlation IDs
   - Performance bottleneck identification

### Alerting and Incident Response

```yml
# prometheus/alert-rules.yml
groups:
- name: novamind-alerts
  rules:
  - alert: HighErrorRate
    expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is above 5% for the last 5 minutes"
  
  - alert: APIHighLatency
    expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{handler!="metrics"}[5m])) by (le)) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "API high latency"
      description: "95th percentile of request duration is above 2 seconds for the last 5 minutes"
  
  - alert: DatabaseConnectionPoolExhausted
    expr: sum(rate(db_connection_pool_exhausted_total[5m])) > 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Database connection pool exhausted"
      description: "Database connection pool has been exhausted"
```

### HIPAA-Compliant Monitoring

1. **PHI Protection**
   - No PHI in logs or metrics
   - Secure access to monitoring tools
   - Audit logging for monitoring access

2. **Compliance Monitoring**
   - Automated compliance checks
   - Regular security scanning
   - Access control verification

## Disaster Recovery and Business Continuity

### Backup Strategy

1. **Database Backups**
   - Automated daily backups
   - Point-in-time recovery
   - Encrypted backup storage
   - Regular restore testing

2. **Configuration Backups**
   - Infrastructure as Code (IaC)
   - Version-controlled configurations
   - Automated deployment pipelines

### Recovery Procedures

1. **Database Recovery**
   - Documented recovery procedures
   - Regular recovery drills
   - RTO and RPO monitoring

2. **System Recovery**
   - Multi-region deployment capability
   - Automated failover procedures
   - Regular disaster recovery testing

## Implementation Guidelines

### Security Best Practices

1. **Secure CI/CD**
   - Secure credential management
   - Signed commits and artifacts
   - Least privilege access for CI/CD systems

2. **Infrastructure Security**
   - Network segmentation
   - Security groups and firewalls
   - Regular vulnerability scanning

3. **Application Security**
   - Dependency scanning
   - SAST and DAST integration
   - Regular penetration testing

### Performance Optimization

1. **Database Optimization**
   - Query performance monitoring
   - Index optimization
   - Connection pooling

2. **API Optimization**
   - Response caching
   - Pagination for large datasets
   - Asynchronous processing for long-running tasks

3. **Frontend Optimization**
   - Code splitting and lazy loading
   - Asset optimization
   - CDN integration

### Implementation Roadmap

1. **Phase 1: Foundation**
   - Set up CI/CD pipeline
   - Implement automated testing
   - Deploy basic monitoring

2. **Phase 2: Enhancement**
   - Implement advanced monitoring
   - Set up disaster recovery
   - Optimize performance

3. **Phase 3: Scaling**
   - Implement horizontal scaling
   - Set up multi-region deployment
   - Enhance security measures
