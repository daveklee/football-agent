# Browser MCP Integration

This project uses [Browser MCP](https://browsermcp.io/) for browser automation instead of Selenium or Playwright.

## What is Browser MCP?

Browser MCP connects AI applications to your browser via a Chrome extension, allowing automation using your existing browser profile. This means:

- ✅ **You stay logged in** - Uses your existing browser cookies and session
- ✅ **Fast** - Automation happens locally on your machine
- ✅ **Private** - Browser activity stays on your device
- ✅ **Stealth** - Avoids basic bot detection by using your real browser fingerprint
- ✅ **No ChromeDriver** - No need to install or manage ChromeDriver

## Installation

### 1. Install Chrome Extension

1. Go to https://browsermcp.io/
2. Click "Add to Chrome"
3. Install the Browser MCP extension

### 2. Verify MCP Configuration

The Browser MCP server is configured in `mcp_config.json`:

```json
{
  "browsermcp": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-browser"
    ]
  }
}
```

This uses the official Browser MCP server package via npx.

## Available Browser MCP Tools

Browser MCP provides these tools via MCP:

- **`mcp_browsermcp_browser_navigate`** - Navigate to a URL
- **`mcp_browsermcp_browser_click`** - Click on elements
- **`mcp_browsermcp_browser_type`** - Type text into editable elements
- **`mcp_browsermcp_browser_snapshot`** - Capture accessibility snapshot of current page
- **`mcp_browsermcp_browser_screenshot`** - Take a screenshot
- **`mcp_browsermcp_browser_hover`** - Hover over elements
- **`mcp_browsermcp_browser_press_key`** - Press keyboard keys
- **`mcp_browsermcp_browser_go_back`** - Go back to previous page
- **`mcp_browsermcp_browser_go_forward`** - Go forward to next page
- **`mcp_browsermcp_browser_wait`** - Wait for specified time
- **`mcp_browsermcp_browser_get_console_logs`** - Get browser console logs
- **`mcp_browsermcp_browser_drag_and_drop`** - Drag and drop elements

## How It Works

1. **Extension Installation**: The Browser MCP Chrome extension is installed in your browser
2. **MCP Server**: The Browser MCP server (configured in `mcp_config.json`) connects to the extension
3. **Agent Usage**: The agent uses Browser MCP tools to automate browser actions
4. **Your Browser**: Actions happen in your actual Chrome browser using your profile

## Usage in This Project

The agent's `BrowserAutomationTools` class provides high-level functions that use Browser MCP under the hood:

- `set_lineup()` - Sets lineup changes
- `add_player()` - Adds players from waiver wire
- `drop_player()` - Drops players
- `propose_trade()` - Proposes trades
- `accept_trade()` / `reject_trade()` - Handles trade offers
- `navigate_to_yahoo_fantasy()` - Navigates to Yahoo Fantasy pages
- `take_screenshot()` - Takes screenshots

All of these functions use Browser MCP tools to interact with Yahoo Fantasy Football.

## Workflow Example

When the agent needs to set a lineup:

1. **Navigate**: Uses `mcp_browsermcp_browser_navigate` to go to lineup page
2. **Snapshot**: Uses `mcp_browsermcp_browser_snapshot` to see page structure
3. **Interact**: Uses `mcp_browsermcp_browser_click` or `drag_and_drop` to move players
4. **Save**: Uses `mcp_browsermcp_browser_click` to click save button

All actions happen in your browser, so you can see what's happening in real-time.

## Benefits Over Selenium

| Feature | Browser MCP | Selenium |
|---------|------------|----------|
| Login State | Uses your existing session | Requires login automation |
| Setup | Just install extension | Install ChromeDriver, manage versions |
| Detection | Uses real browser fingerprint | Can be detected as automation |
| Performance | Local, fast | Can be slower |
| Privacy | All local | All local |

## Troubleshooting

### Extension Not Working

- Make sure the Browser MCP extension is installed and enabled
- Check that the extension has necessary permissions
- Restart Chrome if needed

### MCP Server Not Connecting

- Verify `mcp_config.json` is correct
- Check that `npx` is available (comes with Node.js)
- Review MCP server logs for errors

### Browser Actions Not Working

- Make sure you're logged into Yahoo Fantasy Football in Chrome
- Browser MCP uses your existing session, so you need to be logged in first
- Try navigating manually to verify you're logged in

## Documentation

- **Browser MCP Website**: https://browsermcp.io/
- **Browser MCP Documentation**: https://docs.browsermcp.io/
- **MCP Protocol**: https://modelcontextprotocol.io/

## Security Notes

- Browser MCP automation happens locally on your machine
- Your browser activity is not sent to remote servers
- The extension only works when the MCP server is connected
- Always review agent actions before allowing automatic execution

