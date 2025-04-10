# Comprehensive Test Suite Implementation for Novamind Digital Twin

## PROJECT CONTEXT

The Novamind Digital Twin is a HIPAA-compliant psychiatry platform that requires extensive testing across all layers of the application. This prompt will guide you through implementing a comprehensive test suite to ensure 100% production readiness.

## SYSTEM ANALYSIS

Let's examine the current project structure:

```
<use_mcp_tool>
<server_name>backendFileSystem</server_name>
<tool_name>directory_tree</tool_name>
<arguments>{"path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/app"}
</arguments>
</use_mcp_tool>
```

Let's understand the clean architecture principles applied in this project:

```
<use_mcp_tool>
<server_name>backendFileSystem</server_name>
<tool_name>read_file</tool_name>
<arguments>{"path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/docs/10_CLEAN_ARCHITECTURE.md"}
</arguments>
</use_mcp_tool>
```

And let's examine the HIPAA compliance requirements:

```
<use_mcp_tool>
<server_name>backendFileSystem</server_name>
<tool_name>read_file</tool_name>
<arguments>{"path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/docs/20_HIPAA_COMPLIANCE.md"}
</arguments>
</use_mcp_tool>
```

## TEST INVENTORY

Let's identify what tests already exist:

```
<use_mcp_tool>
<server_name>backendFileSystem</server_name>
<tool_name>directory_tree</tool_name>
<arguments>{"path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/app/tests"}
</arguments>
</use_mcp_tool>
```

## TEST IMPLEMENTATION PLAN

Based on the analysis, implement the following test categories:

### 1. Standalone Tests (No External Dependencies)

For each core domain entity, implement tests that:
- Validate entity creation
- Check all validation rules
- Test edge cases
- Ensure proper behavior without external dependencies

Example command for implementing a standalone test:

```
<use_mcp_tool>
<server_name>backendFileSystem</server_name>
<tool_name>write_file</tool_name>
<arguments>
{
  "path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/app/tests/standalone/test_standalone_[entity_name].py",
  "content": "\"\"\"Standalone test for [Entity Name]\n\nThis module contains both the implementation and tests for the [Entity Name]\nin a single file, making it completely independent of the rest of the application.\n\"\"\"\n\nimport unittest\nimport pytest\nfrom datetime import datetime\nfrom enum import Enum\nfrom typing import Dict, List, Optional, Any\nfrom uuid import uuid4\n\n\n# ============= [Entity Name] Implementation =============\n\n# Implementation code here\n\n\n# ============= [Entity Name] Tests =============\n\n@pytest.mark.standalone\nclass Test[EntityName](unittest.TestCase):\n    \"\"\"Test the [Entity Name] class.\"\"\"\n    \n    def setUp(self):\n        \"\"\"Set up for each test.\"\"\"\n        pass\n        \n    def test_creation(self):\n        \"\"\"Test creating an [Entity Name].\"\"\"\n        pass\n        \n    def test_validation(self):\n        \"\"\"Test validation rules.\"\"\"\n        pass\n        \n    # Additional tests here\n"
}
</arguments>
</use_mcp_tool>
```

### 2. venv_only Tests (Python Packages but No External Services)

Implement tests that require Python packages but no external services:

```
<use_mcp_tool>
<server_name>backendFileSystem</server_name>
<tool_name>write_file</tool_name>
<arguments>
{
  "path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/app/tests/venv_only/test_venv_[service_name].py",
  "content": "\"\"\"venv_only test for [Service Name]\n\nThis test requires Python packages but no external services.\n\"\"\"\n\nimport pytest\nimport pandas as pd\nimport numpy as np\nfrom unittest.mock import MagicMock, patch\n\nfrom app.application.services import [ServiceName]\n\n@pytest.mark.venv_only\ndef test_[service_name]_processing():\n    \"\"\"Test that [Service Name] properly processes data.\"\"\"\n    # Arrange\n    # Mock any dependencies\n    \n    # Act\n    # Call the service\n    \n    # Assert\n    # Verify results\n"
}
</arguments>
</use_mcp_tool>
```

### 3. Integration Tests (External Services like Databases)

```
<use_mcp_tool>
<server_name>backendFileSystem</server_name>
<tool_name>write_file</tool_name>
<arguments>
{
  "path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/app/tests/integration/test_integration_[component].py",
  "content": "\"\"\"Integration test for [Component Name]\n\nThis test requires external services like databases.\n\"\"\"\n\nimport pytest\nfrom unittest.mock import MagicMock, patch\n\nfrom app.domain.entities import [Entity]\nfrom app.infrastructure.repositories import [Repository]\n\n@pytest.mark.integration\ndef test_[component]_integration():\n    \"\"\"Test [Component Name] integration with external services.\"\"\"\n    # Arrange\n    # Set up test database or mock external services\n    \n    # Act\n    # Call the component with dependencies\n    \n    # Assert\n    # Verify results\n    \n    # Cleanup\n    # Clean up test data\n"
}
</arguments>
</use_mcp_tool>
```

### 4. HIPAA Compliance Tests

```
<use_mcp_tool>
<server_name>backendFileSystem</server_name>
<tool_name>write_file</tool_name>
<arguments>
{
  "path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/app/tests/security/test_phi_[component].py",
  "content": "\"\"\"HIPAA compliance test for [Component Name]\n\nTests ensure proper handling of PHI in accordance with HIPAA regulations.\n\"\"\"\n\nimport pytest\nfrom unittest.mock import MagicMock, patch\n\nfrom app.core.security import [SecurityComponent]\n\n@pytest.mark.security\n@pytest.mark.phi\ndef test_phi_sanitization_[component]():\n    \"\"\"Test that PHI is properly sanitized in [Component Name].\"\"\"\n    # Arrange\n    # Set up test data with PHI\n    \n    # Act\n    # Call the component that should sanitize PHI\n    \n    # Assert\n    # Verify PHI is properly sanitized\n"
}
</arguments>
</use_mcp_tool>
```

## EXECUTION AND VERIFICATION

Run the standalone tests:

```
<execute_command>
<command>cd /workspaces/Novamind-Backend-ONLY-TWINS && ./backend/scripts/run_standalone_tests.sh</command>
</execute_command>
```

Run the venv_only tests:

```
<execute_command>
<command>cd /workspaces/Novamind-Backend-ONLY-TWINS && ./backend/scripts/run_venv_tests.sh</command>
</execute_command>
```

## KNOWLEDGE CAPTURE

Store your findings in the memory system:

```
<use_mcp_tool>
<server_name>memory</server_name>
<tool_name>create_entities</tool_name>
<arguments>
{
  "entities": [
    {
      "name": "TestCoverage",
      "entityType": "QualityAssurance",
      "observations": [
        "Document test coverage findings here",
        "List components with good coverage",
        "Identify gaps in test coverage"
      ]
    }
  ]
}
</arguments>
</use_mcp_tool>
```

## PRODUCTION READINESS CHECKLIST

- All domain entities have standalone tests
- All services have appropriate tier tests
- All API endpoints have integration tests
- All HIPAA compliance features have security tests
- Code coverage meets minimum threshold (>80%)
- No security vulnerabilities identified
- PHI handling follows HIPAA guidelines
- Error handling is comprehensive
- Logging follows security best practices
- Performance under load is acceptable

After completing test implementation, run the full production readiness check.