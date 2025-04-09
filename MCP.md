# MCP Filesystem Server Setup (Novamind Project)

This document outlines the steps to set up and run the standard MCP filesystem server for use with the Novamind project in this Codespace environment.

## Prerequisites

*   Node.js and npm installed.
*   `npx` available.

## Setup Steps

1.  **Create Server Directory and Files:**
    *   Ensure the base directory exists:
        ```bash
        mkdir -p /home/codespace/.local/share/Roo-Code/MCP
        ```
    *   Navigate into the directory:
        ```bash
        cd /home/codespace/.local/share/Roo-Code/MCP
        ```
    *   Use the `@modelcontextprotocol/create-server` tool to scaffold the server. You can customize the name and description if desired (the example uses `novamind-filesystem`):
        ```bash
        npx @modelcontextprotocol/create-server filesystem-server --name novamind-filesystem --description "Filesystem server for Novamind"
        ```

2.  **Install Dependencies and Build:**
    *   Navigate into the newly created server directory:
        ```bash
        cd filesystem-server
        ```
    *   Install required npm packages:
        ```bash
        npm install
        ```
    *   Build the server executable:
        ```bash
        npm run build
        ```
    *   This creates the executable file at `build/index.js`.

3.  **Configure Global MCP Settings:**
    *   Edit the global MCP settings file: `/home/codespace/.vscode-remote/data/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json`
    *   Add or ensure the following entry exists within the `mcpServers` object:
        ```json
        {
          "mcpServers": {
            "novamind-filesystem": {
              "command": "node",
              "args": [
                "/home/codespace/.local/share/Roo-Code/MCP/filesystem-server/build/index.js"
              ],
              "env": {},
              "disabled": false,
              "alwaysAllow": [] // Add specific tool names here if needed, e.g., ["list_files", "read_file"]
            }
            // Add other servers here if necessary
          }
        }
        ```

## Running the Server

*   Open a terminal in VS Code.
*   Run the server executable directly using Node.js:
    ```bash
    node /home/codespace/.local/share/Roo-Code/MCP/filesystem-server/build/index.js
    ```
*   **Important:** This command runs the server in the foreground. It needs to remain running in that terminal for the MCP tools to be available. Do not close the terminal or stop the process (e.g., with Ctrl+C) if you intend to use the filesystem tools.

## Verification

*   After starting the server, you can ask the AI assistant (like Roo or the Transcendent Triad) to test the connection using a tool, for example:
    ```xml
    <use_mcp_tool>
    <server_name>novamind-filesystem</server_name>
    <tool_name>list_files</tool_name>
    <arguments>
    {
      "path": ".",
      "recursive": false
    }
    </arguments>
    </use_mcp_tool>
    ```
*   A successful response indicates the server is running and configured correctly. An error like "Not connected" usually means the server process is not running.