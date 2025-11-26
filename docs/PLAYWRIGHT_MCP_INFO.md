# Playwright MCP Information

This agent uses [Playwright MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/playwright) for browser automation.

## Setup

1. **Install Playwright MCP**:
   The agent expects the `@playwright/mcp` package to be available via `npx`.
   
   ```bash
   npx @playwright/mcp --help
   ```

2. **Configuration**:
   The `mcp_config.json` file should be configured to use the Playwright MCP server:

   ```json
   {
     "mcpServers": {
       "playwright-extension": {
         "command": "npx",
         "args": [
           "-y",
           "@playwright/mcp@latest"
         ]
       }
     }
   }
   ```

## Usage

The agent will automatically use Playwright MCP tools when it needs to interact with the browser (e.g., setting lineups, adding players).

The available tools are:
- `playwright_navigate`: Navigate to a URL
- `playwright_click`: Click on elements
- `playwright_fill`: Type text into fields
- `playwright_screenshot`: Take screenshots
- `playwright_hover`: Hover over elements
- `playwright_evaluate`: Execute JavaScript

## Troubleshooting

If the agent fails to connect to Playwright MCP:
1. Check if `npx` is installed and available in your PATH.
2. Check if you can run `npx @playwright/mcp` manually.
3. Check the logs for any error messages related to MCP connection.
