# MCP Health Check

This prompt verifies that the MCP servers are properly configured and accessible.

## File System MCP Check

Let's first check if we can access the backend file system:

```
<use_mcp_tool>
<server_name>backendFileSystem</server_name>
<tool_name>list_allowed_directories</tool_name>
<arguments>{}</arguments>
</use_mcp_tool>
```

Now let's check if we can read a file:

```
<use_mcp_tool>
<server_name>backendFileSystem</server_name>
<tool_name>read_file</tool_name>
<arguments>{"path": "/workspaces/Novamind-Backend-ONLY-TWINS/backend/pytest.ini"}</arguments>
</use_mcp_tool>
```

## Memory MCP Check

Let's check if we can access the memory system:

```
<use_mcp_tool>
<server_name>memory</server_name>
<tool_name>read_graph</tool_name>
<arguments>{}</arguments>
</use_mcp_tool>
```

Let's create a test entity:

```
<use_mcp_tool>
<server_name>memory</server_name>
<tool_name>create_entities</tool_name>
<arguments>
{
  "entities": [
    {
      "name": "MCPHealthCheck",
      "entityType": "SystemTest",
      "observations": [
        "MCP Health check executed successfully",
        "File system MCP is accessible",
        "Memory MCP is accessible"
      ]
    }
  ]
}
</arguments>
</use_mcp_tool>
```

## Test Execution Check

Let's verify we can run a command:

```
<execute_command>
<command>cd /workspaces/Novamind-Backend-ONLY-TWINS && python -m pytest backend/app/tests/standalone/ --collect-only | grep "standalone" | wc -l</command>
</execute_command>
```

## Summary

If all the above commands execute successfully, your MCP configuration is working correctly. You can now use the provided prompt templates to implement and execute tests for production readiness:

1. Use `full-test-suite-implementation.md` for comprehensive test implementation
2. Execute tests with `./backend/scripts/run_all_tests.sh`
3. Review test results and fix any issues

The system is set up with:
- Standalone tests (no external dependencies)
- venv_only tests (Python packages but no external services)
- Integration tests (external services)
- Security tests (HIPAA compliance)

All test tiers have proper execution scripts and reporting.