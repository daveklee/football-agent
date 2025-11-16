"""League rules memory management aligned with ADK MemoryService best practices."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.adk.events.event import Event
from google.adk.memory.base_memory_service import BaseMemoryService
from google.adk.sessions.session import Session
from google.genai import types as genai_types

logger = logging.getLogger(__name__)


def _build_content(text: str) -> genai_types.Content:
    return genai_types.Content(role="assistant", parts=[genai_types.Part(text=text)])


class LeagueRulesMemory:
    """Stores league rules locally and synchronizes them with an ADK MemoryService."""

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        *,
        memory_service: Optional[BaseMemoryService] = None,
        app_name: str = "football-agent",
    ):
        if storage_dir is None:
            project_root = Path(__file__).parent.parent.parent
            storage_dir = str(project_root)

        self.storage_dir = Path(storage_dir)
        self.memory_file = self.storage_dir / ".league_rules_memory.json"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._session_cache: Dict[str, Dict[str, Any]] = {}
        self._memory: Dict[str, Dict[str, Any]] = self._load_memory()
        self._memory_service = memory_service
        self._app_name = app_name

    def _load_memory(self) -> Dict[str, Dict[str, Any]]:
        if not self.memory_file.exists():
            logger.info(f"League rules memory file not found at {self.memory_file}")
            return {}

        try:
            with open(self.memory_file, "r") as f:
                memory = json.load(f)
            logger.info(f"Loaded league rules memory for {len(memory)} league(s)")
            return memory
        except Exception as e:
            logger.error(f"Error loading league rules memory: {e}")
            return {}

    def _save_memory(self) -> None:
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self._memory, f, indent=2)
            logger.info(f"Saved league rules memory to {self.memory_file}")
        except Exception as e:
            logger.error(f"Error saving league rules memory: {e}")

    def _normalize_rules(self, league_id: str, league_info: Dict[str, Any]) -> Dict[str, Any]:
        league_name = league_info.get("league") or league_info.get("name", "")
        return {
            "league_id": league_id,
            "scoring_type": league_info.get("scoring_type", "Unknown"),
            "roster_positions": league_info.get("roster_positions", []),
            "scoring_settings": league_info.get("scoring_settings", {}),
            "position_eligibility": league_info.get("position_eligibility", {}),
            "num_teams": league_info.get("num_teams"),
            "season": league_info.get("season"),
            "league_name": league_name,
            "discovered_at": league_info.get("discovered_at"),
            "raw_data": league_info,
        }

    async def store_league_rules(self, league_id: str, league_info: Dict[str, Any]) -> bool:
        try:
            stored_rules = self._normalize_rules(league_id, league_info)
            self._memory[league_id] = stored_rules
            self._session_cache[league_id] = stored_rules
            self._save_memory()

            if self._memory_service:
                await self._ingest_into_memory_service(league_id, stored_rules)

            logger.info(
                "Stored league rules for %s (scoring=%s, positions=%s)",
                league_id,
                stored_rules.get("scoring_type"),
                len(stored_rules.get("roster_positions", [])),
            )
            return True
        except Exception as e:
            logger.error(f"Error storing league rules: {e}")
            return False

    async def _ingest_into_memory_service(self, league_id: str, rules: Dict[str, Any]) -> None:
        if not self._memory_service:
            return
        summary_text = self.format_rules_for_agent(league_id) or json.dumps(rules, indent=2)
        event = Event(author="league_rules_tool", content=_build_content(summary_text))
        session = Session(
            id=f"league-rules-{league_id}",
            appName=self._app_name,
            userId=league_id,
            events=[event],
        )
        await self._memory_service.add_session_to_memory(session)

    def get_league_rules(self, league_id: str) -> Optional[Dict[str, Any]]:
        if league_id in self._session_cache:
            return self._session_cache[league_id]
        rules = self._memory.get(league_id)
        if rules:
            self._session_cache[league_id] = rules
        return rules

    def has_league_rules(self, league_id: str) -> bool:
        return self.get_league_rules(league_id) is not None

    def get_all_leagues(self) -> Dict[str, Dict[str, Any]]:
        return self._memory.copy()

    def clear_league_rules(self, league_id: Optional[str] = None) -> None:
        if league_id:
            self._memory.pop(league_id, None)
            self._session_cache.pop(league_id, None)
        else:
            self._memory.clear()
            self._session_cache.clear()
        self._save_memory()

    def format_rules_for_agent(self, league_id: str) -> str:
        rules = self.get_league_rules(league_id)
        if not rules:
            return ""

        formatted = f"\n=== LEAGUE RULES (League: {rules.get('league_name', league_id)}) ===\n"
        formatted += f"Scoring Type: {rules.get('scoring_type', 'Unknown')}\n"

        scoring_type = rules.get("scoring_type", "").lower()
        if "ppr" in scoring_type:
            formatted += "⚠️ PPR League: Pass-catching players are MORE valuable\n"
        elif "half" in scoring_type:
            formatted += "⚠️ Half-PPR League: Pass-catchers get moderate boost\n"
        else:
            formatted += "→ Standard scoring: TD-dependent players prioritized\n"

        roster_positions = rules.get("roster_positions", [])
        if roster_positions:
            formatted += "\nRoster Positions:\n"
            position_counts: Dict[str, int] = {}
            for pos in roster_positions:
                pos_name = pos.get("position") if isinstance(pos, dict) else str(pos)
                count = pos.get("count", 1) if isinstance(pos, dict) else 1
                if pos_name and pos_name.upper() not in ["BN", "BE", "BENCH", "IR"]:
                    position_counts[pos_name] = position_counts.get(pos_name, 0) + count

            for pos, count in sorted(position_counts.items()):
                formatted += f"  - {pos}: {count}\n"
                if pos.upper() in ["SUPERFLEX", "OP"]:
                    formatted += "    ⚠️ SUPERFLEX: QBs are MUCH more valuable!\n"

        formatted += "\n"
        return formatted

    def search_league_rules(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results: List[Dict[str, Any]] = []
        for payload in self._memory.values():
            if query_lower in json.dumps(payload).lower():
                results.append(payload)
        return results

