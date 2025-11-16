# Tool Compatibility Notes

## Gemini Function Calling Limitation

**Important**: Gemini models do NOT support mixing custom FunctionTools with built-in ADK tools (like `google_search`) in the same agent.

### The Problem

If you try to use both:
- Custom FunctionTools (like our Yahoo, Browser, Analysis tools)
- Built-in ADK tools (like `google_search`)

You'll get this error:
```
400 INVALID_ARGUMENT: Tool use with function calling is unsupported
```

### The Solution

We've removed the `google_search` built-in tool and use only custom FunctionTools.

### Current Tool Configuration

- ✅ **21 Custom FunctionTools**:
  - 9 Yahoo Fantasy tools
  - 8 Browser automation tools  
  - 4 Analysis tools
- ❌ **No built-in tools** (removed `google_search` to avoid conflict)

### Alternatives for Web Search

If you need web search functionality:

1. **Use Browser MCP tools**:
   - Navigate to search engines or news sites
   - Use `mcp_browsermcp_browser_navigate` to go to URLs
   - Use `mcp_browsermcp_browser_snapshot` to read page content

2. **Use Yahoo Fantasy MCP Server**:
   - The server includes built-in data sources
   - Some tools may include news/sentiment analysis

3. **Create a separate agent** (advanced):
   - Create a sub-agent dedicated to web search
   - Use agent-to-agent communication for search tasks

### References

- [ADK Python Issue #134](https://github.com/google/adk-python/issues/134)
- [Google Cloud Medium Article](https://medium.com/google-cloud/expanding-adk-ai-agent-capabilities-with-tools-008a929d1ffb)

