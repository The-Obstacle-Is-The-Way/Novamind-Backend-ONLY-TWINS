# Novamind Digital Twin Testing & Production Readiness

## Context & Goals

You are tasked with completing the implementation of a comprehensive test suite and preparing the Novamind Digital Twin psychiatry platform for production. This system requires HIPAA compliance, robust testing, and high-quality implementation following clean architecture principles.

Your primary focus will be:
1. Building on the existing standalone tests
2. Implementing the next tier of tests (venv_only tests)
3. Ensuring all critical components have thorough test coverage
4. Preparing the system for production deployment

## Initial Analysis Instructions

1. First, use the backendFileSystem MCP to explore the project structure:
   ```
   <use_mcp_tool>
   <server_name>backendFileSystem</server_name>
   <tool_name>directory_tree</tool_name>
   <arguments>{"path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend"}
   </arguments>
   </use_mcp_tool>
   ```

2. Then, read and analyze all documentation files to understand architectural principles and requirements:
   ```
   <use_mcp_tool>
   <server_name>backendFileSystem</server_name>
   <tool_name>read_multiple_files</tool_name>
   <arguments>{"paths": [
     "/workspaces/Novamind-Backend-ONLY-TWINS/backend/docs/10_CLEAN_ARCHITECTURE.md",
     "/workspaces/Novamind-Backend-ONLY-TWINS/backend/docs/20_HIPAA_COMPLIANCE.md",
     "/workspaces/Novamind-Backend-ONLY-TWINS/backend/docs/10_SYSTEM_DESIGN.md"
   ]}
   </arguments>
   </use_mcp_tool>
   ```

3. Check the existing standalone tests to understand current coverage:
   ```
   <use_mcp_tool>
   <server_name>backendFileSystem</server_name>
   <tool_name>list_directory</tool_name>
   <arguments>{"path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/app/tests/standalone"}
   </arguments>
   </use_mcp_tool>
   ```

4. Analyze the pytest configuration to understand test categorization:
   ```
   <use_mcp_tool>
   <server_name>backendFileSystem</server_name>
   <tool_name>read_file</tool_name>
   <arguments>{"path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/pytest.ini"}
   </arguments>
   </use_mcp_tool>
   ```

## Knowledge Management with Memory MCP

As you analyze the system, store key information using the memory MCP:

1. Create entities for major system components:
   ```
   <use_mcp_tool>
   <server_name>memory</server_name>
   <tool_name>create_entities</tool_name>
   <arguments>
   {
     "entities": [
       {
         "name": "DomainLayer",
         "entityType": "Architecture",
         "observations": ["Key domain entities and their validation logic", "Core business rules"]
       },
       {
         "name": "TestingStrategy",
         "entityType": "Quality",
         "observations": ["Current test categories and markers", "Test isolation approach"]
       }
     ]
   }
   </arguments>
   </use_mcp_tool>
   ```

2. Create relationships between components:
   ```
   <use_mcp_tool>
   <server_name>memory</server_name>
   <tool_name>create_relations</tool_name>
   <arguments>
   {
     "relations": [
       {
         "from": "TestingStrategy",
         "to": "DomainLayer",
         "relationType": "validates"
       }
     ]
   }
   </arguments>
   </use_mcp_tool>
   ```

## Implementation Tasks

Based on your analysis, implement the following in order:

1. Create additional standalone tests for any critical domain entities that lack coverage
2. Implement the `venv_only` test tier:
   - Create a `conftest.py` for venv_only tests
   - Migrate appropriate tests from integration to venv_only category
   - Ensure tests are properly marked and isolated 
3. Implement database test fixtures that allow for isolated testing with SQLite in-memory databases
4. Create CI/CD workflow configuration for running all test tiers

## HIPAA Compliance Verification 

Ensure all tests related to HIPAA compliance are properly implemented:

1. PHI sanitization tests
2. Audit logging tests
3. Authentication and authorization tests
4. Data encryption tests

## Production Readiness Verification

Create a production readiness checklist that verifies:

1. All critical components have test coverage
2. No sensitive data is logged or exposed
3. All endpoints have proper authentication and authorization
4. Database migrations work correctly
5. Error handling is comprehensive

## Documentation

Update the test documentation to reflect the new structure and coverage.

## File Organization

Keep all new standalone tests in the `/backend/app/tests/standalone/` directory.
Keep all new venv_only tests in the `/backend/app/tests/venv_only/` directory.

## Development Context

This is a psychiatry digital twin platform that must maintain HIPAA compliance while providing sophisticated ML-powered analytics. All code must follow clean architecture principles with proper separation of concerns.