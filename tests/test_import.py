
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from app.agent import FantasyFootballAgent
    print("Successfully imported FantasyFootballAgent")
except Exception as e:
    print(f"Failed to import FantasyFootballAgent: {e}")
    sys.exit(1)
