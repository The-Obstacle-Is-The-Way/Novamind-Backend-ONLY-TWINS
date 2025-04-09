# CORE_ARCHITECTURE

## Overview

NOVAMIND is a premium, HIPAA-compliant concierge psychiatry platform designed for a solo provider practice with potential for future growth. This document outlines the architectural approach, design patterns, and implementation guidelines for this luxury psychiatric platform.

The platform is designed as an end-to-end stack using a single best-in-class service or library for each component, ensuring full HIPAA compliance and fitting a solo provider's needs (initially ~$500/month, scalable as the practice grows). The backend is built in Python (FastAPI), with the AWS ecosystem as the primary infrastructure provider for compliance and integration, except where a third-party tool is clearly superior (and still HIPAA-capable).

## Core Architectural Philosophy

NOVAMIND follows Clean Architecture principles to ensure separation of concerns, maintainability, and testability. This architectural approach enables us to build a system that is both robust and flexible, capable of evolving with the needs of a high-end psychiatric practice.

### SOLID Principles Application

- **Single Responsibility**: Each class has one responsibility (e.g., `PatientRepository` only handles patient data access)
- **Open/Closed**: Extend behavior without modifying code (e.g., adding new appointment types)
- **Liskov Substitution**: Implementations interchangeable with their interfaces
- **Interface Segregation**: Focused interfaces prevent dependency bloat
- **Dependency Inversion**: High-level modules independent of low-level implementations

## Architectural Layers

```text
┌───────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                             │
│  (API Controllers, Web UI, CLI, GraphQL Resolvers)                │
├───────────────────────────────────────────────────────────────────┤
│                    APPLICATION LAYER                              │
│  (Use Cases, Services, DTOs, Validators)                          │
├───────────────────────────────────────────────────────────────────┤
│                      DOMAIN LAYER                                 │
│  (Entities, Value Objects, Repository Interfaces, Domain Services)│
├───────────────────────────────────────────────────────────────────┤
│                       DATA LAYER                                  │
│  (Repository Implementations, ORM, External Services)             │
└───────────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### Domain Layer

- Contains business entities and logic
- Defines repository interfaces
- Implements domain services and value objects
- Has no dependencies on other layers
- Represents psychiatry-relevant concepts: Patients, Appointments, Billing, Outcomes, Notes, etc.
- Contains all logic regarding patient flow, scheduling rules, and therapy features

### Application Layer

- Implements use cases and orchestrates workflows
- Transforms domain objects to/from DTOs
- Handles validation and business rules
- Depends only on the Domain Layer
- Coordinates complex operations across multiple domain entities

### Data Layer

- Implements repository interfaces from Domain Layer
- Handles persistence and external service integration
- Manages database transactions and caching
- Depends on the Domain Layer but not on Application Layer
- Implements ORM (SQLAlchemy) but keeps it separate from the Domain layer

### Presentation Layer

- Handles HTTP requests and responses
- Implements authentication and authorization
- Manages user interfaces and API endpoints
- Depends on the Application Layer
- Uses Pydantic v2 schemas for input/output validation
- Leverages FastAPI's `Depends()` for dependency injection

## Directory Structure

```text
novamind/
├── app/
│   ├── core/                    # Core utilities and configuration
│   │   ├── config.py            # Application configuration
│   │   └── utils/               # Shared utilities
│   │       ├── logging.py       # Logging utilities
│   │       ├── encryption.py    # Encryption utilities
│   │       └── validation.py    # Validation utilities
│   ├── domain/                  # Domain Layer
│   │   ├── entities/            # Domain entities
│   │   ├── repositories/        # Repository interfaces
│   │   ├── services/            # Domain services
│   │   └── value_objects/       # Value objects
│   ├── application/             # Application Layer
│   │   ├── services/            # Application services
│   │   ├── dtos/                # Data Transfer Objects
│   │   └── validators/          # Input validators
│   ├── infrastructure/          # Data Layer
│   │   ├── persistence/         # Database implementations
│   │   │   ├── models/          # ORM models
│   │   │   └── repositories/    # Repository implementations
│   │   └── services/            # External service integrations
│   └── presentation/            # Presentation Layer
│       ├── api/                 # API endpoints
│       │   ├── routes/          # Route handlers
│       │   └── docs/            # API documentation
│       └── web/                 # Web interface
│           ├── templates/       # HTML templates
│           └── static/          # Static assets
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── e2e/                     # End-to-end tests
└── alembic/                     # Database migrations
```

## Design Patterns

1. **Repository Pattern**: Abstracts data access logic
2. **Dependency Injection**: Manages dependencies between components
3. **Factory Pattern**: Creates complex objects
4. **Strategy Pattern**: Implements different algorithms
5. **Observer Pattern**: Implements event handling
6. **Adapter Pattern**: Connects incompatible interfaces
7. **Command Pattern**: Encapsulates requests as objects

## Design Patterns Integration

NOVAMIND implements several design patterns to ensure clean, maintainable code:

- **Factory Pattern**: For creating complex domain objects (e.g., `PatientFactory`, `AppointmentFactory`)
- **Repository Pattern**: Data access abstraction (e.g., `PatientRepository`, `AppointmentRepository`)
- **Strategy Pattern**: For interchangeable algorithms (e.g., billing strategies, notification methods, AI-based modules like risk scoring or summarization)
- **Observer Pattern**: For event handling (e.g., appointment created/changed notifications, triggering analytics when patient records change)
- **Command Pattern**: For operations that need audit trail (e.g., patient record changes)
- **Factory/Abstract Factory**: For creating complex domain aggregates (e.g., building a patient record with multiple sub-objects, handling default settings)

## Cloud Infrastructure

- **Frontend Hosting**: AWS Amplify (S3 & CloudFront) - Provides simple CI/CD from a git repo and hosts static sites in a HIPAA-eligible environment
- **Backend Hosting & Orchestration**: AWS ECS Fargate - Containerizes the FastAPI app with container orchestration (scaling, self-healing) without managing servers
- **CI/CD Pipeline**: AWS CodePipeline & CodeBuild - Automates deployments from code commits and runs tests/builds Docker images

## Technology Stack

### Core Technology Components

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| API Framework | FastAPI | 0.104.0+ | High-performance REST API with automatic documentation |
| Data Validation | Pydantic V2 | 2.0.0+ | Data validation, serialization, and schema definition |
| ORM | SQLAlchemy | 2.0.0+ | Database operations via repository pattern |
| Database | PostgreSQL | 14.0+ | HIPAA-compliant primary data store |
| Authentication | AWS Cognito | via boto3 | User management with MFA support |
| File Storage | AWS S3 | via boto3 | Encrypted file storage |
| Task Queue | Celery | 5.3.0+ | Background task processing |
| Message Broker | Redis | 7.0.0+ | Support for event-driven architecture |
| Testing | pytest | 7.0.0+ | Comprehensive test suite |
| Migrations | Alembic | 1.12.0+ | Database schema versioning |
| Messaging | Twilio for SMS | HIPAA-compliant | Patient notifications and reminders |
| Email | AWS SES | via boto3 | Email communications |
| Form System | JotForm HIPAA-Enforced Plan | - | Clinical questionnaires and intake forms |
| Analytics | Amazon QuickSight | - | Interactive dashboards and data visualization |
| Hosting | AWS ECS Fargate | - | Containerized deployment |
| CI/CD | AWS CodePipeline & CodeBuild | - | Automated testing and deployment |
| Payments | Stripe | - | Patient payments, subscriptions, and invoices |

### Detailed Stack Components

#### Cloud Infrastructure

- **Frontend Hosting – AWS Amplify (S3 & CloudFront):** Use AWS Amplify Hosting to deploy the clinic's web frontend (e.g., a React SPA) on Amazon S3 behind Amazon CloudFront. Amplify provides simple CI/CD from a git repo and hosts static sites in a HIPAA-eligible environment. Content is delivered over HTTPS via CloudFront for low-latency worldwide access. *Cost:* Amplify and CloudFront have low pay-as-you-go costs; for small scale, expect only a few dollars per month for hosting (Amplify includes 1000 build minutes and 15 GB serves on free tier). *HIPAA:* AWS Amplify Console is listed as a HIPAA-eligible service, and with an AWS BAA in place, S3/CloudFront will encrypt data in transit and at rest.

- **Backend Hosting & Orchestration – AWS ECS Fargate:** Containerize the FastAPI app and deploy on Amazon ECS (Elastic Container Service) using Fargate (serverless containers). ECS handles container orchestration (scaling, self-healing) without managing servers. Fargate tasks run in an isolated VPC, and an Application Load Balancer (ALB) routes HTTPS traffic to FastAPI. This setup is fully managed and scales on-demand. *Cost:* Fargate charges by CPU/memory seconds; a small always-on service (e.g., 0.25 vCPU, 0.5GB) might cost ~$20-30/month initially, and can scale out automatically with load. ECS itself has no additional cost, and using Fargate avoids EC2 instance charges when idle. *HIPAA:* Amazon ECS is HIPAA-eligible and commonly used in compliant architectures. All PHI stays within the AWS environment. Ensure the ALB uses AWS Certificate Manager for TLS so data is encrypted in transit.

- **CI/CD Pipeline – AWS CodePipeline & CodeBuild:** Use AWS CodePipeline to automate deployments from code commits, and CodeBuild to run tests/build Docker images. Both services are HIPAA-eligible. CodePipeline orchestrates the process (with one active pipeline free in AWS Free Tier) and costs only ~$1/month per pipeline thereafter. CodeBuild charges by the minute (with a generous free tier of 100 build minutes/month). For a solo project, these costs are negligible. *HIPAA:* With AWS BAA, CI/CD services can be used as long as they don't handle PHI in the pipeline. Using AWS for CI/CD keeps all deployment steps within a compliant boundary.

#### Database

- **Relational Database – Amazon RDS (PostgreSQL):** Use AWS RDS PostgreSQL for the primary data store. RDS is a fully managed relational database service that is HIPAA-eligible and provides built-in encryption, backups, and scalability. Enable encryption at rest with an AWS KMS customer-managed key so all data, snapshots, and replicas are encrypted using AES-256. Enforce SSL/TLS for data in transit. RDS allows setting up automatic backups and Multi-AZ replication for high availability. PostgreSQL is flexible and powerful for structured health data (patients, appointments, notes, etc.) and supports JSON for unstructured fields if needed. *Cost:* A small DB instance (e.g., db.t3.small) with storage encryption is ~$50/month; you can start with single-AZ to save cost (~$25/mo) and scale to Multi-AZ or a larger instance as the practice grows. As volume increases, RDS can scale vertically, or migrate to Amazon Aurora (compatible with PostgreSQL) for better performance without code changes. *HIPAA:* Amazon RDS is explicitly HIPAA eligible. With a BAA, ePHI can be stored in RDS as long as access controls are in place. The data is protected via encryption at rest (KMS) and in transit (SSL). Audit the DB access via CloudTrail and RDS logs for compliance.

#### Authentication

- **User Auth – Amazon Cognito:** Implement user sign-up, login, and identity management with AWS Cognito. Cognito User Pools handle user registration, password resets, and JWT token issuance out-of-the-box. It supports multi-factor authentication (MFA) via SMS or email OTP, and even TOTP apps. You can define roles/groups (e.g., "patient", "admin") and Cognito will include these in token claims for role-based access control, so FastAPI can enforce authorization logic (e.g., only providers see analytics, patients see their data). Cognito supports OAuth2 flows and integrates with FastAPI by validating the issued JWT access tokens in middleware. *Cost:* Amazon Cognito has a free tier for 50k monthly active users. Beyond that, it costs ~$0.0055 per monthly active user – for a solo practice with maybe hundreds of patients at most, the cost is only a few dollars a month. MFA SMS messages incur a small fee via Amazon SNS (~$0.006 each), which is negligible for occasional 2FA. *HIPAA:* Amazon Cognito is HIPAA-eligible, meaning it can be used to manage accounts that have access to PHI. It stores user credentials (which are not PHI) securely with hashing, and offers advanced security features (like risk-based adaptive authentication). Ensure you sign an AWS BAA and use Cognito's secure features (enforce strong passwords, enable MFA). All communication with Cognito is over HTTPS, and JWTs are signed with RSA keys. The FastAPI app should verify tokens using Cognito's public keys to secure endpoints.

#### File & Document Storage

- **Patient File Storage – Amazon S3:** Use Amazon S3 for storing uploaded documents (intake forms, lab PDFs, insurance cards, etc.) and any binary data. S3 is a durable, scalable object storage and is HIPAA-eligible. Create a dedicated S3 bucket for patient files with default encryption (SSE-KMS) so all data at rest is encrypted by AWS KMS (using your managed keys). Access to the bucket should be strictly controlled via IAM policies – the FastAPI backend will generate pre-signed URLs for clients to upload or download files securely, ensuring that only authorized users can access specific objects. *Cost:* S3 storage is very cheap (roughly $0.023 per GB/month). For example, storing 100 GB of scans would cost about $2.30/month. Data transfer out (e.g., patients downloading files) is $0.09/GB, but using CloudFront can reduce egress costs for frequently accessed files. Initially, expect well under $10/month unless storing huge volumes of imaging. *HIPAA:* Amazon S3 with a BAA can store ePHI (it's commonly used for medical images and documents). S3 provides auditing (via Access Logs or CloudTrail events for each access) for compliance. To meet HIPAA requirements, bucket versioning can be enabled (to retain old versions of files) and MFA Delete can add an extra layer of protection against accidental deletion. All file transfers will be over HTTPS (SSL) – either via the pre-signed URL or through your FastAPI proxy – ensuring encryption in transit. With these configurations, S3 fully safeguards PHI files in a compliant manner.

#### Clinical Communication

- **SMS & Email Notifications – Twilio (Programmable Messaging):** For patient communications like appointment reminders, scheduling notifications, or check-in messages, Twilio is the chosen platform. Twilio's Programmable Messaging API enables sending SMS (and MMS) reliably, and they offer a secure healthcare compliance program. With a signed Business Associate Agreement (BAA), Twilio's HIPAA-eligible services (programmable SMS/MMS, voice, etc.) can be used to transmit PHI. Use SMS for appointment reminders or brief notifications; Twilio supports features like message templates, delivery status tracking, and two-way messaging if you want patients to confirm or reply. For email, avoid sending PHI directly – for example, send a generic notice like "You have a new secure message" rather than detailed medical info. *Cost:* Twilio SMS in the US costs about $0.0075 per message, and a dedicated phone number ~$1/month. If you send 500 texts in a month, that's only ~$3.75. Twilio has a free trial and volume discounts at scale. Email notifications (without PHI) could use Amazon SES (which is HIPAA-eligible) at ~$0.0001 per email. The total communications cost for a solo practice is easily under $20/month initially. *HIPAA:* Twilio will sign a BAA (available on their Enterprise plan) to cover SMS/MMS in a HIPAA capacity. Under that agreement, you must use only HIPAA-supported products and follow Twilio's guidelines (e.g., disable message logging that might store PHI). As a safeguard, limit content in messages to the minimum necessary: e.g., "Appointment reminder for [Patient First Name] on [Date/Time]" – this is allowed by HIPAA as a health care operation communication. For any detailed messaging, use the app's secure messaging feature rather than standard SMS or email.

#### Form System

- **Online Forms – JotForm (HIPAA-Enforced Plan):** Use JotForm to create and embed secure online forms for clinical questionnaires and intake. JotForm is a mature form-builder that offers a HIPAA-compliant solution on its Gold plan (with BAA). This allows the solo provider to digitize forms like PHQ-9 (depression screening), GAD-7 (anxiety screening), intake and consent forms, etc., with minimal coding. JotForm provides a drag-and-drop form editor and many templates, so you can quickly configure medically themed forms. In HIPAA mode, form data is encrypted end-to-end: JotForm automatically encrypts submissions and files in transit and at rest. Patients can fill out forms on their phone or computer through a mobile-friendly interface, and their responses are stored securely. The FastAPI backend can use JotForm's API (HIPAA endpoint) to pull submission data into the app (or receive webhook notifications when a form is completed). *Cost:* JotForm's Gold plan is ~$99/month, which includes HIPAA compliance and a high submission limit. This fits within the ~$500 budget. This cost covers unlimited form building and up to tens of thousands of submissions – plenty for a solo practice. As the practice scales, JotForm Enterprise is available for more customization. *HIPAA:* JotForm will sign a BAA and enable a special HIPAA setting on the account. When enabled, all form fields containing health info are marked as "PHI" and are handled with extra care (e.g., hidden in email notifications). The data is stored in an isolated HIPAA-compliant server environment. JotForm's HIPAA compliance means the provider inherits strong security: encryption keys, audit logs, and access controls are managed to HIPAA standards. By using JotForm, the provider can deploy complex forms (with skip logic, e-signatures, file uploads, etc.) without writing custom code, and be confident that patient data from those forms is protected.

#### Analytics

- **Analytics Dashboards – Amazon QuickSight:** Use Amazon QuickSight for interactive dashboards and data visualization. QuickSight is a fully managed BI service by AWS that is HIPAA-eligible and can embed real-time visuals into your application. It allows you to create charts, graphs, and KPI dashboards for both clinical metrics (e.g., patient outcomes, symptom scores over time) and business metrics (e.g., revenue, appointments) in a single interface. QuickSight can directly connect to the RDS PostgreSQL database or read from curated data in S3. It features visual, real-time dashboards with ML insights and the ability to ask natural language questions (with the Q feature) – though for initial needs, standard visuals suffice. You can embed QuickSight dashboards into the FastAPI frontend for the provider's admin view, so that the psychiatrist sees up-to-date metrics whenever they log in. QuickSight offers row-level security, so if in the future multiple providers or a patient-facing dashboard is needed, you can restrict data per user. *Cost:* QuickSight has two pricing modes. For authors (who create dashboards) it's $18/user/month (annual) or $24 month-to-month. For viewers, it offers pay-per-session pricing: $0.30 per 30-minute session, capped at $5 per user per month. In a solo scenario, the psychiatrist can be both author and viewer of their data, so one user license (~$18) may cover it. As the practice scales to more staff or if you embed for many patients, the per-session model keeps costs low (only pay when dashboards are actually used). *HIPAA:* Amazon QuickSight is on the HIPAA eligible list, meaning AWS has attested its compliance with HIPAA security controls. All dashboard data stays within AWS. For extra compliance, you can apply encryption to QuickSight SPICE in-memory data stores and ensure any data exports are handled properly. QuickSight leverages AWS security (IAM for access control, CloudTrail for auditing dashboard access). It also supports fine-grained access (so, in future, if patients have a portal, one could embed a personal progress chart to a patient and be assured they can only see their own data).

#### EMR System Features

- **Electronic Medical Records – Custom FastAPI + Integrations:** The platform itself will implement core EMR functionality, augmented by specific integrations for labs and e-prescribing. For note-taking and patient records, use a rich text editor in the frontend (e.g., TipTap or Quill in a React app) and store the resulting notes in the PostgreSQL database. Each clinical note can be stored as structured text (e.g., Markdown or HTML) along with metadata (author, timestamps). To achieve versioning and audit trails, the backend will not overwrite notes but rather append new versions: e.g., use an "edits" table or a version column, or a library like SQLAlchemy-Continuum to automatically version record changes. This provides an immutable history of what changes were made to a note and when – satisfying HIPAA's record integrity requirements. The system can generate a timeline view of patient activity by querying events (appointments, forms submitted, notes written, medications prescribed) sorted by date. This gives a chronological record of the patient's care.

- **Lab/Imaging Integration:** For Lab/Imaging Orders & Results, integrate with the Redox API platform. Redox is a healthcare integration SaaS that connects your application to many EHRs, lab systems (LabCorp, Quest, hospital labs), and imaging centers through one standardized API. Instead of dealing with HL7 messages or custom lab interfaces, you send orders and receive results via Redox in JSON format, and Redox handles translation to/from the lab's system. Redox supports 80+ EHRs and health systems and offers data models for orders, results, referrals, etc. For example, when you order a lab test for a patient, you'd call Redox's Orders API; Redox securely delivers it to the lab's system (via HL7 or FHIR) and routes the result back to your app when ready. Similarly, for imaging, you can place an order for an MRI and receive the radiologist's report through Redox. Redox acts as a hub, greatly simplifying interoperability.

- **E-Prescribing and Prior Auth:** For e-Prescribing and Prior Auth, you can leverage Redox to connect with pharmacy networks or use a specialized eRx service. One option is integrating with DrFirst or Surescripts via Redox (Redox has connections for medication prescribing workflows). Another approach is using SureScripts' network indirectly – e.g., certain EHR integrations through Redox will allow sending prescriptions that pharmacies receive via SureScripts. Prior authorizations can be handled via integration with services like CoverMyMeds (which has an API for electronic prior auth); Redox's network may also facilitate this if the PA is initiated through the EHR.

#### Payments

- **Payments & Billing – Stripe:** Use Stripe to handle patient payments, subscriptions, and invoices for the practice's services. Stripe is a developer-friendly payment platform that supports subscription billing, invoicing, and stored payment methods (via Stripe Billing and Customer Portal). While Stripe itself does not sign BAAs and isn't "HIPAA certified", it can still be used in a HIPAA-compliant manner solely for payment processing, which is considered outside of HIPAA's scope. According to HHS guidance, collecting payment is a healthcare operation but exempt from HIPAA regulations that require a BAA, as long as the service is only used to process payments. Many HIPAA-compliant telehealth platforms use Stripe under this exemption. *How to use Stripe safely:* Limit Stripe's use to just the minimum necessary financial info (card numbers, names, and basic service descriptors). Do not send detailed treatment information or PHI in the Stripe transaction metadata. For instance, you might charge for "Therapy Session #1234" rather than "PTSD counseling session with Dr. Smith on 2025-03-01". By keeping descriptions generic, we ensure no sensitive diagnosis or condition info is in Stripe. Stripe will handle the credit card securely (PCI DSS compliant) and deposit to your bank. We can use Stripe's Python SDK to create customers and subscriptions – e.g., set up a monthly membership fee or per-visit charge. Stripe Invoicing can send patients a bill via email; however, since those emails come from Stripe and could contain service info, ensure they are generic (or turn off Stripe's automatic emails and send your own notices through the portal). *Cost:* Stripe's fees are standard: 2.9% + 30¢ per successful charge. There's no monthly fee for basic use. Stripe Billing for subscriptions adds 0.5% on recurring payments. So for a $200 session, Stripe would take about $6.20. Assuming $10k monthly revenue, fees ~$300 – this scales with usage. There is no upfront cost, and no cost if you have no transactions.

### Package Dependency Management

```
# requirements.txt

# Core Framework
fastapi==0.104.0
uvicorn[standard]==0.23.2
pydantic==2.4.2
python-multipart==0.0.6
python-dotenv==1.0.0

# Database
sqlalchemy==2.0.23
alembic==1.12.0
asyncpg==0.28.0  # Async PostgreSQL driver
psycopg2-binary==2.9.9  # Sync PostgreSQL driver

# Security & Authentication
python-jose[cryptography]==3.3.0  # JWT tokens
passlib[bcrypt]==1.7.4  # Password hashing
boto3==1.28.65  # AWS SDK for Cognito, S3, etc.
cryptography==41.0.4  # General cryptographic operations

# Background Tasks & Event Handling
celery==5.3.4
redis==5.0.1
aioredis==2.0.1  # Async Redis client

# Testing
pytest==7.4.2
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
hypothesis==6.88.1  # Property-based testing

# Development Tools
black==23.9.1
flake8==6.1.0
mypy==1.6.1
pre-commit==3.5.0
bandit==1.7.5  # Security linting
safety==2.3.5  # Dependency vulnerability checking

# Logging & Monitoring
structlog==23.2.0
opentelemetry-api==1.20.0
opentelemetry-sdk==1.20.0

# AWS Specific
boto3-stubs[cognito,s3,ses]==1.28.65  # Type hints for boto3
```

### HIPAA Compliance Matrix

| Component | HIPAA Requirement | Implementation |
|-----------|-------------------|----------------|
| Authentication | Access Controls (§164.312(a)(1)) | AWS Cognito with MFA |
| Data Storage | Encryption (§164.312(a)(2)(iv)) | PostgreSQL with TDE, S3 with SSE |
| API Access | Transmission Security (§164.312(e)(1)) | HTTPS, JWT with short expiry |
| Auditing | Audit Controls (§164.312(b)) | Structured logging with PHI filtering |
| Backup | Contingency Plan (§164.308(a)(7)) | Automated PostgreSQL backups |

## AI Layer

- **Mental Health Analysis Model**: MentaLLaMA-33B-lora (hosted on AWS GPU instances, e.g., SageMaker or EC2)
- **PHI Detection**: AWS Comprehend Medical (used to detect and mask PHI identifiers *before* sending text data to MentaLLaMA)
- **Use Cases**:
  - Risk assessment (e.g., suicidality) from patient text
  - Interpretable mental health analysis (sentiment, psycho-linguistic indicators)
  - Rationale generation for classifications
  - Contextual support suggestions
  - Potential for clinical note summarization (requires careful prompting and validation)

## Security & HIPAA Compliance

### HIPAA Compliance Requirements

1. **Authentication and Authorization**: Role-based access control with AWS Cognito
2. **Encryption**: All PHI encrypted at rest (via AWS KMS) and in transit (TLS 1.2/1.3)
3. **Audit Logging**: Comprehensive audit trails for all PHI access via CloudTrail and application-level logging
4. **Data Validation**: Strict validation for all input data using Pydantic schemas
5. **Error Handling**: Secure error handling without exposing PHI
6. **Session Management**: Secure session handling with timeouts
7. **Backup and Recovery**: Regular backups with secure storage

### Security Implementation

- **Encryption Everywhere**: All data at rest is encrypted using AWS KMS managed keys
- **Identity & Access Management**: AWS IAM roles and policies to enforce least privilege access
- **Web Application Firewall (WAF)**: AWS WAF to filter malicious traffic
- **Monitoring & Logging**: Amazon CloudWatch for monitoring server logs and setting alarms
- **Key Management & Secrets**: AWS Secrets Manager for storing sensitive secrets
- **Audit Trail & Activity Logs**: Detailed audit logs for all user actions

## Third-Party Integrations

- **EMR Features**: Custom FastAPI implementation with rich text editor for notes
- **Lab/Imaging Integration**: Redox API platform for connecting to lab systems and imaging centers
- **E-Prescribing**: Integration with pharmacy networks via Redox or specialized eRx services
- **Prior Authorization**: Integration with services like CoverMyMeds

## Scalability & Performance

- The architecture is designed to scale from a single provider to multiple providers or clinics
- AWS services provide on-demand scaling capabilities
- Database can scale vertically or migrate to Amazon Aurora as volume increases
- Containerized deployment allows for easy horizontal scaling

## Implementation Sequence

The implementation of the NOVAMIND platform follows a structured sequence to ensure that each layer builds upon a solid foundation:

1. **Domain Layer** - Core business entities and logic
2. **Data Layer** - Database models and repositories
3. **Application Layer** - Services and use cases
4. **API Layer** - FastAPI routes and schemas
5. **Authentication & Security** - HIPAA compliance implementation
6. **Infrastructure Components** - AWS service integrations
7. **Testing & Quality Assurance** - Testing strategy and implementation

Each layer is implemented with a focus on maintainability, testability, and HIPAA compliance. The sequence ensures that the core business logic is established first, followed by the data access layer, then the application services, and finally the presentation layer.

## Summary: Canonical Stack Selection

The NOVAMIND platform uses a carefully selected stack of technologies and services to create a HIPAA-compliant, high-performance system:

- **Cloud Infrastructure:** AWS Amplify (hosting static frontend on S3/CloudFront) + AWS ECS Fargate (FastAPI backend containers) with AWS CodePipeline/CodeBuild (CI/CD)
- **Database:** Amazon RDS – PostgreSQL (encrypted with KMS, Multi-AZ)
- **Authentication:** Amazon Cognito (user pools with JWT, MFA, role-based groups)
- **File Storage:** Amazon S3 (secure bucket for files, SSE-KMS encryption, pre-signed URL access)
- **Communication:** Twilio API (HIPAA-enabled SMS for reminders; minimal PHI in email notices)
- **Form System:** JotForm HIPAA (online forms with BAA, data encrypted end-to-end)
- **Analytics:** Amazon QuickSight (embedded BI dashboards, pay-per-session pricing)
- **EMR Features:** Custom FastAPI EMR (rich text notes with versioning) + Redox API (lab/imaging results, eRx integration)
- **AI Layer:** MentaLLaMA-33B-lora (hosted on AWS GPU instances for mental health analysis) + AWS Comprehend Medical (PHI scrubbing before analysis)
- **Security:** AWS Security Suite – KMS encryption, IAM, CloudTrail logs, AWS WAF firewall & rate limiting, CloudWatch monitoring, GuardDuty & Security Hub checks
- **Payments:** Stripe (credit card processing & subscriptions; used only for payments to stay HIPAA-exempt)

Each of these choices is production-grade and scalable. Starting under ~$500/month, this stack delivers a premium, secure software experience for a concierge psychiatric practice, while laying the groundwork for growth (additional providers, more patients, integrations) without major refactoring.