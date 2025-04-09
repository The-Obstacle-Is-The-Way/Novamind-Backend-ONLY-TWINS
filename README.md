# Novamind Digital Twin Backend

## Overview

Novamind Digital Twin is a next-generation psychiatric platform built on a revolutionary architecture that combines three powerful AI components (the "Trinity Stack"):

1. **MentalLLaMA-33B**: Advanced language model for clinical text understanding and reasoning
2. **XGBoost Prediction Engine**: Sophisticated prediction and optimization engine
3. **PAT (Pretrained Actigraphy Transformer)**: Deep analysis of physiological and behavioral data

This repository contains the backend code for the Novamind Digital Twin platform, with a focus on clean architecture, HIPAA compliance, and advanced clinical reasoning capabilities.

## Architecture

The system follows Clean Architecture principles with strict separation of concerns:
- **Domain Layer**: Pure business logic (entities, repositories, service interfaces)
- **Infrastructure Layer**: Implementation of services, data access, external integrations
- **Application Layer**: Use cases orchestrating the services
- **Presentation Layer**: API endpoints and UI components

## Key Features

- Temporal Knowledge Graph representation of clinical data
- Bayesian Belief Network for probabilistic reasoning with uncertainty quantification
- Multimodal data fusion from clinical notes, physiological measurements, and behavioral patterns
- Treatment effect mapping and prediction
- Digital phenotype detection
- Counterfactual simulation of intervention scenarios

## Getting Started

See the [documentation](./backend/docs/README.md) for detailed instructions on setting up and running the system.

## Security and Compliance

This system is designed with HIPAA compliance as a core principle. See [security documentation](./backend/docs/HIPAA_COMPLIANCE.md) for details.
