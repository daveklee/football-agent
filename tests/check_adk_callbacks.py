
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from google.adk.agents import CallbackContext
    print("Successfully imported CallbackContext")
    print("ADK_CALLBACKS_AVAILABLE should be True")
except ImportError as e:
    print(f"Failed to import CallbackContext: {e}")
    print("ADK_CALLBACKS_AVAILABLE should be False")

try:
    from app.agent import ADK_CALLBACKS_AVAILABLE
    print(f"Actual ADK_CALLBACKS_AVAILABLE: {ADK_CALLBACKS_AVAILABLE}")
except Exception as e:
    print(f"Failed to import ADK_CALLBACKS_AVAILABLE: {e}")
