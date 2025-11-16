# Model Configuration Notes

## Function Calling Support

**Important**: Not all Gemini models support function calling (ADK FunctionTools).

### Models That Support Function Calling
- ✅ **gemini-2.5-pro** - Full function calling support (for ADK FunctionTools)
- ✅ **gemini-2.0-flash-exp** - Supports function calling
- ✅ **gemini-1.5-pro** - Supports function calling

### Models That Do NOT Support Function Calling
- ❌ **gemini-2.5-flash** - Does NOT support ADK FunctionTools
- ❌ **gemini-2.0-flash** - Does NOT support function calling

## Current Configuration

This project is configured to use **gemini-2.5-flash** by default for cost savings:
1. MCP servers work independently via `mcp_config.json` (don't require function calling)
2. Yahoo Fantasy MCP Server provides tools via MCP protocol
3. Browser MCP Server provides tools via MCP protocol
4. The agent uses MCP tools directly, not ADK FunctionTools
5. Flash is faster and cheaper than Pro

## Changing the Model

If you want to use a different model, update the `MODEL_NAME` environment variable in your `.env` file:

```bash
# Current: Flash for cost savings (MCP servers work independently)
MODEL_NAME=gemini-2.5-flash

# For ADK FunctionTools support (if you add custom tools)
MODEL_NAME=gemini-2.5-pro

# Alternative models with function calling
MODEL_NAME=gemini-2.0-flash-exp
MODEL_NAME=gemini-1.5-pro
```

## Error: "Tool use with function calling is unsupported"

If you see this error, it means you're trying to use ADK FunctionTools with Flash.

**Solution**: 
- Remove FunctionTools from agent initialization (already done)
- Use MCP servers configured in `mcp_config.json` instead
- MCP tools work independently and don't require function calling

## Model Comparison

| Model | ADK FunctionTools | MCP Tools | Speed | Cost | Use Case |
|-------|------------------|-----------|-------|------|----------|
| gemini-2.5-pro | ✅ Yes | ✅ Yes | Medium | Higher | Agents with ADK FunctionTools |
| gemini-2.5-flash | ❌ No | ✅ Yes | Fast | Lower | Agents using MCP servers (current) |
| gemini-2.0-flash-exp | ✅ Yes | ✅ Yes | Fast | Medium | Agents with ADK FunctionTools (experimental) |

**Note**: MCP servers work with ALL models because they use the MCP protocol, not ADK FunctionTools.

## References

- [Gemini API Function Calling Documentation](https://ai.google.dev/gemini-api/docs/function-calling)
- [ADK Python Issue #134](https://github.com/google/adk-python/issues/134)

