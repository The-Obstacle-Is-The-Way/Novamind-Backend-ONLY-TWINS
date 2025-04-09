# Import Path Standardization for Trinity Stack Components

## Overview

This document addresses import path issues that have been identified in the Trinity Stack components. Resolving these issues will ensure all components can be properly imported and used throughout the codebase.

## Current Issues

Analysis of the codebase has revealed inconsistent import patterns, particularly between the "refactored" Trinity Stack components and their dependencies. Notable issues include:

1. **Absolute imports with project prefix**:
   - Imports like `from backend.app.domain.entities.refactored.digital_twin_core import ...` include the project name `backend` prefix, which creates environment-dependent imports

2. **Duplicate interface files**:
   - Multiple interface files exist for the same components (e.g., `pat_interface.py` and `interface.py` in the same directory)
   
3. **Inconsistent module organization**:
   - Some Trinity components reside in `core/services/ml/` while others are in `domain/services/refactored/trinity_stack/`

## Import Path Standardization

### 1. Remove Project Name from Import Paths

**Current problematic pattern**:
```python
from backend.app.domain.entities.refactored.digital_twin_core import (
    ClinicalInsight, TemporalPattern, ClinicalSignificance
)
```

**Standardized pattern**:
```python
from app.domain.entities.refactored.digital_twin_core import (
    ClinicalInsight, TemporalPattern, ClinicalSignificance
)
```

or, preferably, use relative imports:

```python
from ....entities.refactored.digital_twin_core import (
    ClinicalInsight, TemporalPattern, ClinicalSignificance
)
```

### 2. Consolidate Interface Files

Consolidate duplicate interface files to have a single source of truth:

1. Review all interface files in the codebase
2. Determine which version has the most up-to-date API
3. Merge any unique methods from other versions
4. Update all imports to reference the canonical interface

### 3. Standardize Component Organization

Establish a consistent organization pattern for all Trinity Stack components:

| Component | Primary Location | Interface Location |
|-----------|------------------|-------------------|
| MentalLLaMA | `app/domain/services/trinity_stack/mentallama/` | `app/domain/services/trinity_stack/mentallama_service.py` |
| PAT | `app/domain/services/trinity_stack/pat/` | `app/domain/services/trinity_stack/pat_service.py` |
| XGBoost | `app/domain/services/trinity_stack/xgboost/` | `app/domain/services/trinity_stack/xgboost_service.py` |
| Digital Twin Core | `app/domain/services/trinity_stack/digital_twin/` | `app/domain/services/trinity_stack/digital_twin_service.py` |

## Implementation Steps

### Step 1: Fix Import Paths

Create a utility script to automatically update import paths:

```python
#!/usr/bin/env python3

import os
import re
from pathlib import Path

def fix_imports(directory):
    """
    Fix imports in all Python files in the given directory.
    Removes 'backend.' prefix from imports.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Replace 'from backend.app.' with 'from app.'
                updated_content = re.sub(
                    r'from\s+backend\.app\.', 
                    'from app.', 
                    content
                )
                
                # Replace 'import backend.app.' with 'import app.'
                updated_content = re.sub(
                    r'import\s+backend\.app\.', 
                    'import app.', 
                    updated_content
                )
                
                if content != updated_content:
                    with open(file_path, 'w') as f:
                        f.write(updated_content)
                    print(f"Fixed imports in {file_path}")

if __name__ == "__main__":
    # Fix imports in backend/app directory
    fix_imports("backend/app")
```

### Step 2: Resolve Duplicate Interfaces

1. **Analyze interfaces**:
   ```bash
   find backend/app -name "*interface*.py" | sort
   ```

2. **Compare interface versions**:
   For each set of duplicate interfaces, run a diff to identify differences:
   ```bash
   diff backend/app/core/services/ml/pat_interface.py backend/app/core/services/ml/pat/interface.py
   ```

3. **Consolidate to canonical versions**:
   Create merged versions that preserve all functionality.

4. **Update imports**:
   Update all imports to reference the canonical interfaces.

### Step 3: Standardize Directory Structure

1. **Create standardized directory structure**:
   ```bash
   mkdir -p backend/app/domain/services/trinity_stack/{mentallama,pat,xgboost,digital_twin}
   ```

2. **Move implementations to standardized locations**:
   ```bash
   # Example for PAT
   cp -r backend/app/core/services/ml/pat/* backend/app/domain/services/trinity_stack/pat/
   ```

3. **Update imports**:
   After moving files, update all imports to reference the new locations.

4. **Remove duplicate implementations**:
   Only after confirming the new structure works, remove the old implementations.

## Testing Strategy

To ensure these changes don't break functionality:

1. **Create comprehensive test cases** for each Trinity Stack component
2. **Run tests before and after** changes to verify equivalent behavior
3. **Implement integration tests** to verify component interactions
4. **Create test cases** specifically for import scenarios

## Import Conventions Going Forward

### 1. Module Organization

- **Domain layer**: `app/domain/` contains all domain models, interfaces, and services
- **Infrastructure layer**: `app/infrastructure/` contains implementations
- **API layer**: `app/api/` contains API endpoints
- **Core layer**: `app/core/` contains shared utilities and cross-cutting concerns

### 2. Import Practices

- **Prefer relative imports** within the same package
- **Use absolute imports** starting with `app.` for cross-package imports
- **Never use project name** (`backend`) in imports
- **Import interfaces** rather than concrete implementations when possible

### 3. Dependency Injection

- **Use dependency injection** for all service dependencies
- **Reference interfaces** rather than concrete implementations
- **Define injection in composition root** not scattered throughout the code

## Special Cases

### Digital Twin Core

The Digital Twin Core is the central integration point for all Trinity components. It should:

1. Define the abstract interfaces for all Trinity components
2. Provide the composition mechanism to integrate the components
3. Maintain the state transition logic between components

To fix import issues specifically for Digital Twin Core:

```python
# Current
from backend.app.domain.entities.refactored.digital_twin_core import (
    ClinicalInsight, TemporalPattern, ClinicalSignificance
)

# Corrected
from app.domain.entities.digital_twin.core import (
    ClinicalInsight, TemporalPattern, ClinicalSignificance
)
```

## Conclusion

Implementing these import path standardizations will ensure consistent, reliable imports throughout the Trinity Stack components, resolving the current issues and establishing a maintainable pattern for future development.

This standardization is a critical step in ensuring the vertical and horizontal integration of the Trinity Stack components, enabling the Digital Twin concept to function as a unified system.