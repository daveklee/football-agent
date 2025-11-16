"""League rules memory management for persistent storage of league-specific settings."""
import json
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LeagueRulesMemory:
    """Manages persistent storage and retrieval of league-specific rules and settings.
    
    This ensures the agent remembers league scoring rules, roster positions, and other
    settings without needing to fetch them every time. League rules are discovered
    from Yahoo Fantasy API and stored locally for quick access.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize league rules memory.
        
        Args:
            storage_dir: Directory to store league rules. Defaults to project root.
        """
        if storage_dir is None:
            # Default to project root (app/utils/ -> app/ -> project root)
            project_root = Path(__file__).parent.parent.parent
            storage_dir = str(project_root)
        
        self.storage_dir = Path(storage_dir)
        self.memory_file = self.storage_dir / ".league_rules_memory.json"
        
        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing memory
        self._memory: Dict[str, Dict[str, Any]] = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Dict[str, Any]]:
        """Load league rules from persistent storage."""
        if not self.memory_file.exists():
            logger.info(f"League rules memory file not found at {self.memory_file}")
            return {}
        
        try:
            with open(self.memory_file, 'r') as f:
                memory = json.load(f)
            logger.info(f"Loaded league rules memory for {len(memory)} league(s)")
            return memory
        except Exception as e:
            logger.error(f"Error loading league rules memory: {e}")
            return {}
    
    def _save_memory(self):
        """Save league rules to persistent storage."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self._memory, f, indent=2)
            logger.info(f"Saved league rules memory to {self.memory_file}")
        except Exception as e:
            logger.error(f"Error saving league rules memory: {e}")
    
    def store_league_rules(self, league_id: str, league_info: Dict[str, Any]) -> bool:
        """Store league rules for a specific league.
        
        Args:
            league_id: The Yahoo Fantasy league ID
            league_info: Complete league information from yahoo_ff_get_league_info
            
        Returns:
            True if successfully stored, False otherwise
        """
        try:
            # Extract and normalize key league settings
            stored_rules = {
                'league_id': league_id,
                'scoring_type': league_info.get('scoring_type', 'Unknown'),
                'roster_positions': league_info.get('roster_positions', []),
                'scoring_settings': league_info.get('scoring_settings', {}),
                'position_eligibility': league_info.get('position_eligibility', {}),
                'num_teams': league_info.get('num_teams'),
                'season': league_info.get('season'),
                'league_name': league_info.get('name', ''),
                'discovered_at': league_info.get('discovered_at'),  # Timestamp if available
                'raw_data': league_info  # Store full data for reference
            }
            
            self._memory[league_id] = stored_rules
            self._save_memory()
            
            logger.info(f"Stored league rules for league {league_id}: {stored_rules.get('league_name', 'Unknown')}")
            logger.info(f"  Scoring: {stored_rules['scoring_type']}")
            logger.info(f"  Positions: {len(stored_rules.get('roster_positions', []))} position types")
            
            return True
        except Exception as e:
            logger.error(f"Error storing league rules: {e}")
            return False
    
    def get_league_rules(self, league_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored league rules for a specific league.
        
        Args:
            league_id: The Yahoo Fantasy league ID
            
        Returns:
            Stored league rules if found, None otherwise
        """
        rules = self._memory.get(league_id)
        if rules:
            logger.info(f"Retrieved stored league rules for league {league_id}")
            return rules
        else:
            logger.info(f"No stored rules found for league {league_id}")
            return None
    
    def has_league_rules(self, league_id: str) -> bool:
        """Check if league rules are stored for a specific league.
        
        Args:
            league_id: The Yahoo Fantasy league ID
            
        Returns:
            True if rules are stored, False otherwise
        """
        return league_id in self._memory
    
    def get_all_leagues(self) -> Dict[str, Dict[str, Any]]:
        """Get all stored league rules.
        
        Returns:
            Dictionary mapping league_id to league rules
        """
        return self._memory.copy()
    
    def clear_league_rules(self, league_id: Optional[str] = None):
        """Clear stored league rules.
        
        Args:
            league_id: Specific league ID to clear, or None to clear all
        """
        if league_id:
            if league_id in self._memory:
                del self._memory[league_id]
                self._save_memory()
                logger.info(f"Cleared rules for league {league_id}")
        else:
            self._memory.clear()
            self._save_memory()
            logger.info("Cleared all league rules")
    
    def format_rules_for_agent(self, league_id: str) -> str:
        """Format stored league rules for inclusion in agent instructions.
        
        Args:
            league_id: The Yahoo Fantasy league ID
            
        Returns:
            Formatted string describing league rules
        """
        rules = self.get_league_rules(league_id)
        if not rules:
            return ""
        
        formatted = f"\n=== LEAGUE RULES (League: {rules.get('league_name', league_id)}) ===\n"
        formatted += f"Scoring Type: {rules.get('scoring_type', 'Unknown')}\n"
        
        # Scoring implications
        scoring_type = rules.get('scoring_type', '').lower()
        if 'ppr' in scoring_type:
            formatted += "⚠️ PPR League: Pass-catching players are MORE valuable\n"
        elif 'half' in scoring_type:
            formatted += "⚠️ Half-PPR League: Pass-catchers get moderate boost\n"
        else:
            formatted += "→ Standard scoring: TD-dependent players prioritized\n"
        
        # Roster positions
        roster_positions = rules.get('roster_positions', [])
        if roster_positions:
            formatted += "\nRoster Positions:\n"
            if isinstance(roster_positions, list):
                position_counts = {}
                for pos in roster_positions:
                    if isinstance(pos, dict):
                        pos_name = pos.get('position', pos.get('type', 'Unknown'))
                        count = pos.get('count', 1)
                    else:
                        pos_name = str(pos)
                        count = 1
                    if pos_name.upper() not in ['BN', 'BE', 'BENCH', 'IR']:
                        position_counts[pos_name] = position_counts.get(pos_name, 0) + count
                
                for pos, count in sorted(position_counts.items()):
                    formatted += f"  - {pos}: {count}\n"
                    if pos.upper() in ['SUPERFLEX', 'OP']:
                        formatted += "    ⚠️ SUPERFLEX: QBs are MUCH more valuable!\n"
        
        formatted += "\n"
        return formatted

