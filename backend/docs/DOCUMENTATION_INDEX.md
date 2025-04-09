# Novamind Digital Twin Platform: Documentation Index

## Overview Documents

| Document | Description |
|----------|-------------|
| [TRINITY_STACK_ARCHITECTURE.md](./TRINITY_STACK_ARCHITECTURE.md) | Comprehensive overview of the Trinity Stack architecture and integration |
| [TRINITY_STACK_INTEGRATION_STATUS.md](./TRINITY_STACK_INTEGRATION_STATUS.md) | Current status of Trinity Stack component integration |
| [TRINITY_STACK_OVERVIEW.md](./TRINITY_STACK_OVERVIEW.md) | High-level overview of the Trinity Stack concept |
| [TRINITY_AI_ARCHITECTURE.md](./TRINITY_AI_ARCHITECTURE.md) | AI architecture principles for the Trinity Stack |
| [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) | Overview of the codebase organization |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Deployment guidelines and infrastructure |

## Digital Twin Core

| Document | Description |
|----------|-------------|
| [ENHANCED_DIGITAL_TWIN_ARCHITECTURE.md](./ENHANCED_DIGITAL_TWIN_ARCHITECTURE.md) | Enhanced architecture for the Digital Twin system |
| [DIGITAL_TWIN_IMPLEMENTATION_ROADMAP.md](./DIGITAL_TWIN_IMPLEMENTATION_ROADMAP.md) | Implementation roadmap and milestones |
| [DIGITAL_TWIN_CURRENT_STATUS.md](./DIGITAL_TWIN_CURRENT_STATUS.md) | Current implementation status |
| [DIGITAL_TWIN_IMPORT_FIXES.md](./DIGITAL_TWIN_IMPORT_FIXES.md) | Guide for resolving import path issues |
| [TEMPORAL_NEUROTRANSMITTER_IMPLEMENTATION.md](./TEMPORAL_NEUROTRANSMITTER_IMPLEMENTATION.md) | Temporal neurotransmitter modeling implementation |

## Trinity Stack Components

### MentalLLaMA
| Document | Description |
|----------|-------------|
| [components/mentallama/TECHNICAL_IMPLEMENTATION.md](./components/mentallama/TECHNICAL_IMPLEMENTATION.md) | Technical implementation details of MentalLLaMA |
| [components/mentallama/CLINICAL_IMPLEMENTATION.md](./components/mentallama/CLINICAL_IMPLEMENTATION.md) | Clinical application guide for psychiatrists |

### PAT (Pretrained Actigraphy Transformer)
| Document | Description |
|----------|-------------|
| [components/pat/SYSTEM_DESIGN.md](./components/pat/SYSTEM_DESIGN.md) | Architectural design of the PAT system |
| [components/pat/clinical/APPLICATIONS_GUIDE.md](./components/pat/clinical/APPLICATIONS_GUIDE.md) | Clinical applications of actigraphy monitoring |

### XGBoost
| Document | Description |
|----------|-------------|
| [components/xgboost/PREDICTION_ENGINE.md](./components/xgboost/PREDICTION_ENGINE.md) | Core predictive modeling engine documentation |
| [components/xgboost/engineering/DATA_PIPELINE.md](./components/xgboost/engineering/DATA_PIPELINE.md) | Data pipeline and feature engineering |

## Architecture & Design

| Document | Description |
|----------|-------------|
| [architecture/README.md](./architecture/README.md) | Architecture overview |
| [architecture/AUTHENTICATION.md](./architecture/AUTHENTICATION.md) | Authentication and authorization architecture |
| [architecture/DOMAIN_MODELS.md](./architecture/DOMAIN_MODELS.md) | Core domain models design |
| [architecture/STORAGE.md](./architecture/STORAGE.md) | Persistent storage architecture |
| [architecture/DEPLOYMENT.md](./architecture/DEPLOYMENT.md) | Deployment infrastructure |

## Research & Implementation

| Document | Description |
|----------|-------------|
| [digital-twin/research/TEMPORAL_DYNAMICS.md](./digital-twin/research/TEMPORAL_DYNAMICS.md) | Research on temporal dynamics in psychiatric care |

## Development & Operations

| Document | Description |
|----------|-------------|
| [README-PRODUCTION.md](./README-PRODUCTION.md) | Production deployment guide |
| [EXECUTIVE_SUMMARY.md](./EXECUTIVE_SUMMARY.md) | Executive summary for stakeholders |

## Documentation Assessment & Migration

| Document | Description |
|----------|-------------|
| [OLD_DOCS_ASSESSMENT.md](./OLD_DOCS_ASSESSMENT.md) | Assessment of old documentation and migration plan |

---

## Documentation Structure

The documentation follows a hierarchical organization:

```
docs/
├── High-level platform documentation
├── components/
│   ├── mentallama/     # MentalLLaMA-specific documentation
│   ├── pat/            # PAT-specific documentation
│   └── xgboost/        # XGBoost-specific documentation
├── architecture/       # Core architectural documents
├── digital-twin/       # Digital Twin specific documentation
├── implementation/     # Implementation guides
├── infrastructure/     # Infrastructure and deployment
└── security/          # Security and HIPAA compliance
```

This organization ensures that:
1. Each component of the Trinity Stack has its dedicated documentation
2. Cross-cutting concerns are addressed in higher-level documents
3. Implementation details are separated from architectural principles
4. Clinical and technical aspects are clearly distinguished