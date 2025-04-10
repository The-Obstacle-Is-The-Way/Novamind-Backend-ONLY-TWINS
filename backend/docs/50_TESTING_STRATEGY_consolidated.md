# Novamind Backend: Consolidated Testing Strategy (SSOT) - v2 (Code-Analyzed)

## 1. Overview

This document defines the Single Source of Truth (SSOT) for the testing strategy and structure for the Novamind Digital Twin Backend. **This version is based on a detailed analysis of the current codebase structure as of 2025-04-10**, resolving ambiguities from legacy documentation. The goal is a unified, clear structure within `/backend/app/tests/` that aligns with Clean Architecture principles and facilitates efficient, comprehensive testing, particularly for HIPAA compliance and security.

## 2. Current Test Structure Analysis (As of 2025-04-10)

Analysis of the `/backend/app/tests/` directory revealed the following structure and key points:

*   **Unified Root:** All existing tests reside under `/backend/app/tests/`. The separate `/backend/tests/` directory mentioned in some legacy docs is confirmed non-existent.
*   **Primary Categories Exist:** Directories for `unit`, `integration`, `security`, `e2e`, `enhanced`, `standalone`, `venv_only`, and `fixtures` are present.
*   **Layered Subdirs:** `unit` and `integration` contain subdirectories roughly corresponding to Clean Architecture layers (`domain`, `application`, `core`, `infrastructure`).
*   **Inconsistencies/Deviations:**
    *   `unit/app/`: Exists but contains no test definitions. Appears redundant.
    *   `integration/persistence/`: Exists but contains no test definitions. Appears redundant.
    *   `integration/core/`: Contains `test_phi_sanitization_integration.py`. These are valid integration tests for a cross-cutting concern (PHI), but the `/core/` subdirectory under `/integration/` is structurally inconsistent with the SSOT. Tests should be moved (likely to `/integration/security/` or `/integration/infrastructure/security/`).
    *   `integration/infrastructure/persistence/sqlalchemy/`: Contains `test_patient_encryption_integration.py`. Valid persistence integration test, but the `/sqlalchemy/` level is unnecessarily nested. Tests should be moved to `/integration/infrastructure/persistence/`.
    *   `unit/core/services/ml/pat/`: Contains PAT service unit tests. This placement under `/core/` seems acceptable if PAT is considered a core ML capability, though `/unit/infrastructure/ml/pat/` might also be suitable depending on implementation details. For now, its current location is accepted but should be reviewed during import fixing.
*   **Import Errors:** The current structure, combined with potential import path issues from the refactor, is causing numerous `ImportError` and `ModuleNotFoundError` issues during test collection.

## 3. Ideal Test Directory Structure (SSOT - Target State)

Based on the code analysis and Clean Architecture best practices, the **target SSOT** for `/backend/app/tests/` is defined as:

```
/backend/app/tests/              # Unified root for all tests
  __init__.py
  conftest.py                    # Global/shared fixtures
  /unit/                         # Unit tests (isolated components)
    /domain/                     # Mirrors /app/domain
    /application/                # Mirrors /app/application
    /core/                       # Mirrors /app/core
    /infrastructure/             # Mirrors /app/infrastructure
      /persistence/
      /security/
      /logging/
      /ml/                       # Includes /pat/ subdirectory if deemed infra
      # ... etc.
  /integration/                  # Integration tests (components working together)
    /api/                        # API endpoint tests
    /application/                # Service/Use Case integration tests
    /infrastructure/             # Infrastructure integration tests
      /persistence/              # Target for DB integration tests (e.g., encryption)
      /security/                 # Target for security integration tests (e.g., PHI flow)
      /ml/
  /security/                     # Dedicated Security & HIPAA Compliance Tests (holistic)
    /audit/
    /encryption/
    /auth/
    /jwt/
    /phi/
    /hipaa/
  /e2e/                          # End-to-end tests
  /enhanced/                     # Enhanced coverage tests
  /standalone/                   # Dependency-free tests
  /venv_only/                    # Tests needing only Python packages
  /fixtures/                     # Shared Pytest fixtures
  # /factories/                  # (Optional: For test data generation)
  # /utils/                      # (Optional: For test utility functions)
```

**Key Principles of this SSOT:**

*   **Unified & Internal:** All tests within `/app/tests/`.
*   **Clear Categories:** Grouped by `unit`, `integration`, `security`, `e2e`, etc.
*   **Layer Alignment:** `unit` and `integration` mirror app layers.
*   **Dedicated Security:** Top-level `/security/` for holistic compliance/security tests.
*   **Streamlined Paths:** Avoids unnecessary nesting.

## 4. Test Categories and Goals

*   **Unit Tests (`/unit/`)**: Verify individual components in isolation. Mock external dependencies.
    *   *Coverage Goal*: 90%+ (Domain: 95%+, Core: 90%+, App/Infra: 85%+)
*   **Integration Tests (`/integration/`)**: Verify component interactions. Use test databases/services where appropriate.
    *   *Coverage Goal*: 80%+ (API Endpoints: 85%+)
*   **Security Tests (`/security/`)**: Verify security controls, HIPAA compliance, PHI handling.
    *   *Coverage Goal*: 95%+ (PHI Handling: 100%)
*   **End-to-End Tests (`/e2e/`)**: Verify complete user workflows and business processes.
    *   *Coverage Goal*: Focus on critical paths.
*   **Enhanced Tests (`/enhanced/`)**: Rigorous testing for critical/complex components.
    *   *Coverage Goal*: 85%+ for targeted components.
*   **Standalone Tests (`/standalone/`)**: Pure Python tests, no external dependencies. Run first in CI.
    *   *Coverage Goal*: High coverage for targeted pure logic.
*   **Venv-Only Tests (`/venv_only/` or marked `@pytest.mark.venv_only`)**: Require Python packages but mock external services/DBs. Run after standalone.

## 5. Test Implementation Guidelines

*   **Naming Conventions:** Files: `test_[module_or_feature].py`. Functions/Methods: `test_[behavior]_[conditions]_[expected_outcome]`.
*   **Structure:** AAA pattern.
*   **Isolation:** Independent tests, use fixtures, clean up state.
*   **Fixtures:** Use `conftest.py` at appropriate levels.
*   **Mocking:** Use `unittest.mock` / `pytest-mock` for unit tests.
*   **Markers:** Use pytest markers (`@pytest.mark.unit`, etc.). Define in `pytest.ini` or `pyproject.toml`.
*   **HIPAA/PHI:** Use synthetic data. Test sanitization/access controls.
*   **Async Code:** Use `pytest-asyncio`.

## 6. Test Execution and CI/CD

*   **Runner:** `pytest` directly or via scripts.
*   **Config:** Centralize in `pyproject.toml`/`pytest.ini`. Set `testpaths = backend/app/tests`.
*   **CI Pipeline:** Standalone -> Venv-Only -> Remaining (Unit, Integration, Security, E2E) -> Coverage -> Security Scans.
*   **Coverage:** Use `pytest-cov`. Aim for 85%+ overall.

## 7. Refactoring Implementation Plan

*   **Goal:** Align the current structure in `/backend/app/tests/` with the SSOT defined in Section 3. Resolve all test collection errors.
*   **Phase 1: Structural Alignment (Requires Confirmation)**
    1.  **Move Tests:**
        *   Move `backend/app/tests/integration/core/test_phi_sanitization_integration.py` to `backend/app/tests/integration/security/test_phi_sanitization_integration.py`.
        *   Move `backend/app/tests/integration/infrastructure/persistence/sqlalchemy/test_patient_encryption_integration.py` to `backend/app/tests/integration/infrastructure/persistence/test_patient_encryption_integration.py`.
    2.  **Remove Empty/Redundant Dirs:**
        *   `backend/app/tests/unit/app/`
        *   `backend/app/tests/integration/core/` (After moving its contents)
        *   `backend/app/tests/integration/persistence/`
        *   `backend/app/tests/integration/infrastructure/persistence/sqlalchemy/` (After moving its contents)
*   **Phase 2: Error Resolution**
    1.  **Run Collection:** Execute `pytest --collect-only -q app/tests/`. Verify `import file mismatch` errors are gone (if structural cleanup resolves them).
    2.  **Fix Imports:** Systematically correct remaining `ImportError` and `ModuleNotFoundError` based on the cleaned SSOT structure. Prioritize core components (`config`, `exceptions`, `utils`) and base test classes. Verify placement of PAT tests (`unit/core/services/ml/pat/`).
    3.  **Ensure Markers:** Add/verify correct pytest markers.
    4.  **Run & Iterate:** Continuously run `pytest --collect-only` and `pytest` to fix errors until the suite collects and runs cleanly.
*   **Phase 3: Documentation Cleanup**
    1.  **Finalize SSOT Doc:** Ensure this document is accurate after fixes.
    2.  **Remove Legacy Docs:** Delete files in `/backend/docs/legacy/testing/`.

## 8. Conclusion

This consolidated strategy, informed by direct codebase analysis, provides the definitive SSOT for testing. Adherence to this structure and plan will lead to a robust, maintainable, and compliant test suite.