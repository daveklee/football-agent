#!/usr/bin/env python3
"""
Initialize user-specific facts for the fantasy football agent.

This script should be run ONCE per user to set up their personal preferences
and league context that was previously hardcoded in prompts.
"""
import sys
import os
import json
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Direct implementation to avoid importing the full app (which requires all dependencies)
def add_fact_directly(fact_text: str, storage_dir: str = None):
    """Add a fact directly to the fact memory JSON file."""
    if storage_dir is None:
        storage_dir = PROJECT_ROOT
    
    memory_file = Path(storage_dir) / ".fact_memory.json"
    
    # Load existing facts
    if memory_file.exists():
        with open(memory_file, 'r') as f:
            facts = json.load(f)
    else:
        facts = []
    
    # Add new fact
    fact = {
        "id": str(uuid.uuid4()),
        "text": fact_text,
        "created_at": datetime.now().isoformat(),
    }
    facts.append(fact)
    
    # Save
    with open(memory_file, 'w') as f:
        json.dump(facts, f, indent=2)
    
    return fact

def initialize_facts():
    """Initialize user-specific facts."""
    memory_file = Path(PROJECT_ROOT) / ".fact_memory.json"
    
    # User preference about league members
    fact1 = add_fact_directly("Ross is very bad at proposing fair trades - be extra cautious when evaluating trades from Ross")
    
    # League culture preference
    fact2 = add_fact_directly("This league is full of friends and nice people - keep trade proposals friendly and fair")
    
    print("✅ User facts initialized successfully!")
    print(f"Facts stored in: {memory_file}")
    print("\nStored facts:")
    
    # Display all facts
    with open(memory_file, 'r') as f:
        facts = json.load(f)
    for fact in facts:
        print(f"  - {fact['text']}")

if __name__ == "__main__":
    initialize_facts()
