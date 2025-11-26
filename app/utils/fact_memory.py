"""Fact memory management for storing useful items and user preferences."""
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FactMemory:
    """Stores simple facts/memories locally in a JSON file."""

    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            # Default to project root
            project_root = Path(__file__).parent.parent.parent
            storage_dir = str(project_root)

        self.storage_dir = Path(storage_dir)
        self.memory_file = self.storage_dir / ".fact_memory.json"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._memory: List[Dict[str, Any]] = self._load_memory()

    def _load_memory(self) -> List[Dict[str, Any]]:
        if not self.memory_file.exists():
            return []

        try:
            with open(self.memory_file, "r") as f:
                memory = json.load(f)
            logger.info(f"Loaded {len(memory)} facts from memory")
            return memory
        except Exception as e:
            logger.error(f"Error loading fact memory: {e}")
            return []

    def _save_memory(self) -> None:
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self._memory, f, indent=2)
            logger.info(f"Saved fact memory to {self.memory_file}")
        except Exception as e:
            logger.error(f"Error saving fact memory: {e}")

    def add_fact(self, text: str) -> str:
        """Add a new fact to memory.
        
        Args:
            text: The fact content to remember.
            
        Returns:
            The ID of the new fact.
        """
        fact_id = str(uuid.uuid4())
        fact = {
            "id": fact_id,
            "text": text,
            "created_at": datetime.now().isoformat(),
        }
        self._memory.append(fact)
        self._save_memory()
        return fact_id

    def get_all_facts(self) -> List[Dict[str, Any]]:
        """Get all stored facts."""
        return self._memory

    def get_formatted_facts(self) -> str:
        """Get all facts formatted as a string for context injection."""
        if not self._memory:
            return ""
            
        formatted = "KNOWN FACTS & PREFERENCES:\n"
        for fact in self._memory:
            formatted += f"- {fact['text']}\n"
        return formatted

    def clear_facts(self) -> None:
        """Clear all facts."""
        self._memory = []
        self._save_memory()
