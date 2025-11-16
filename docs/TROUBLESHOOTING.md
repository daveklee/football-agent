# Troubleshooting Guide

## Error: "Tool use with function calling is unsupported"

### Symptoms
- Error: `400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Tool use with function calling is unsupported', 'status': 'INVALID_ARGUMENT'}}`
- Logs show wrong model (e.g., `gemini-2.0-flash-exp` instead of `gemini-2.5-pro`)

### Root Causes

1. **Wrong Model**: The agent is using a model that doesn't support function calling
   - ❌ `gemini-2.5-flash` - Does NOT support ADK FunctionTools
   - ❌ `gemini-2.0-flash` - Does NOT support function calling
   - ✅ `gemini-2.5-pro` - Supports function calling
   - ✅ `gemini-2.0-flash-exp` - Supports function calling (experimental)

2. **Mixing Built-in and Custom Tools**: Gemini doesn't support mixing custom FunctionTools with built-in ADK tools (like `google_search`)

3. **ADK Web Using Wrong Config**: ADK web might be loading from `adk_config.yaml` or using defaults instead of the Python agent

### Solutions

#### 1. Verify Model Configuration

Check that `app/utils/config.py` has:
```python
model_name: str = Field("gemini-2.5-pro", env="MODEL_NAME")
```

Check that `.env` has (optional, defaults to `gemini-2.5-pro`):
```
MODEL_NAME=gemini-2.5-pro
```

Check that `adk_config.yaml` has:
```yaml
agent:
  model: gemini-2.5-pro
```

#### 2. Verify Agent Uses Explicit Gemini LLM

The agent should create an explicit `Gemini` LLM instance:
```python
from google.adk.models.google_llm import Gemini
llm = Gemini(model=settings.model_name)
super().__init__(model=llm, ...)
```

#### 3. Remove Built-in Tools

Ensure `adk_config.yaml` has:
```yaml
tools: []  # Empty - no built-in tools
```

And in `app/agent.py`, don't add `GoogleSearch()`:
```python
# Don't add this:
# all_tools.append(GoogleSearch())
```

#### 4. Restart ADK Web Server

After making changes:
1. Stop the ADK web server (Ctrl+C)
2. Restart: `make run-web` or `./scripts/start_adk_web.sh`
3. Clear browser cache if needed

#### 5. Verify Agent Loading

Test that the agent loads correctly:
```bash
python -c "from app import root_agent; print(f'Model: {root_agent.model.model}'); print(f'Tools: {len(root_agent.tools)}')"
```

Should show:
- Model: `gemini-2.5-pro`
- Tools: `21` (or your tool count)
- Model type: `<class 'google.adk.models.google_llm.Gemini'>`

### Debugging Steps

1. **Check Python Agent**:
   ```bash
   python -c "from app.agent import root_agent; print(root_agent.model)"
   ```

2. **Check ADK Web Logs**:
   Look for lines like:
   ```
   INFO - google_llm.py:133 - Sending out request, model: gemini-2.5-pro
   ```
   If it shows a different model, ADK web is using wrong config.

3. **Check for Caching**:
   - Clear Python cache: `find . -type d -name __pycache__ -exec rm -r {} +`
   - Restart ADK web server

4. **Verify root_agent Export**:
   ```bash
   python -c "from app import root_agent; print(type(root_agent))"
   ```

### Common Issues

#### Issue: ADK Web Uses Wrong Model
**Solution**: Ensure `app/agent.py` creates explicit `Gemini` LLM instance, not just a string.

#### Issue: Tools Not Compatible Warning
**Warning**: `Tools at indices [0] are not compatible with automatic function calling (AFC)`
**Solution**: Ensure all tools are `FunctionTool` instances, not function declarations.

#### Issue: Model Defaults to Flash
**Solution**: ADK's `Gemini` class defaults to `gemini-2.5-flash`. Always explicitly set `model=settings.model_name` when creating the LLM instance.

### Still Having Issues?

1. Check `MODEL_NOTES.md` for model compatibility
2. Check `TOOL_COMPATIBILITY.md` for tool limitations
3. Review ADK web server logs for detailed error messages
4. Verify all configuration files match expected values

