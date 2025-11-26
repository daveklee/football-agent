"""Database-backed league rules memory using SQLite."""
import json
import logging
from typing import Any, Dict, List, Optional
import sqlalchemy
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

logger = logging.getLogger(__name__)

Base = declarative_base()


class LeagueRule(Base):
    """SQLAlchemy model for league rules."""
    __tablename__ = "league_rules"
    
    league_id = Column(String, primary_key=True)
    league_name = Column(String)
    scoring_type = Column(String)
    roster_positions = Column(Text)  # JSON string
    scoring_settings = Column(Text)  # JSON string
    position_eligibility = Column(Text)  # JSON string
    num_teams = Column(String)
    season = Column(String)
    raw_data = Column(Text)  # JSON string
    discovered_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class DatabaseLeagueRulesMemory:
    """Stores league rules in SQLite database."""
    
    def __init__(self, db_url: str = "sqlite:///sessions.db"):
        """Initialize database-backed league rules storage.
        
        Args:
            db_url: Database URL (defaults to sessions.db)
        """
        self.db_url = db_url
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self._session = Session()
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Initialized database league rules storage at {db_url}")
    
    def _normalize_rules(self, league_id: str, league_info: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize league info into a standard format."""
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
        """Store league rules in the database.
        
        Args:
            league_id: League identifier
            league_info: League information dictionary
            
        Returns:
            True if successful
        """
        try:
            normalized = self._normalize_rules(league_id, league_info)
            
            # Check if exists
            existing = self._session.query(LeagueRule).filter_by(league_id=league_id).first()
            
            if existing:
                # Update existing
                existing.league_name = normalized["league_name"]
                existing.scoring_type = normalized["scoring_type"]
                existing.roster_positions = json.dumps(normalized["roster_positions"])
                existing.scoring_settings = json.dumps(normalized["scoring_settings"])
                existing.position_eligibility = json.dumps(normalized["position_eligibility"])
                existing.num_teams = str(normalized["num_teams"]) if normalized["num_teams"] else None
                existing.season = str(normalized["season"]) if normalized["season"] else None
                existing.raw_data = json.dumps(normalized["raw_data"])
                existing.updated_at = datetime.now()
                logger.info(f"Updated league rules for {league_id}")
            else:
                # Create new
                rule = LeagueRule(
                    league_id=league_id,
                    league_name=normalized["league_name"],
                    scoring_type=normalized["scoring_type"],
                    roster_positions=json.dumps(normalized["roster_positions"]),
                    scoring_settings=json.dumps(normalized["scoring_settings"]),
                    position_eligibility=json.dumps(normalized["position_eligibility"]),
                    num_teams=str(normalized["num_teams"]) if normalized["num_teams"] else None,
                    season=str(normalized["season"]) if normalized["season"] else None,
                    raw_data=json.dumps(normalized["raw_data"]),
                    discovered_at=datetime.fromisoformat(normalized["discovered_at"]) if normalized.get("discovered_at") else datetime.now()
                )
                self._session.add(rule)
                logger.info(f"Created new league rules for {league_id}")
            
            self._session.commit()
            self._cache[league_id] = normalized
            return True
        except Exception as e:
            logger.error(f"Error storing league rules: {e}")
            self._session.rollback()
            return False
    
    def get_league_rules(self, league_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve league rules from database.
        
        Args:
            league_id: League identifier
            
        Returns:
            Dictionary with league rules, or None if not found
        """
        # Check cache first
        if league_id in self._cache:
            return self._cache[league_id]
        
        try:
            rule = self._session.query(LeagueRule).filter_by(league_id=league_id).first()
            if not rule:
                return None
            
            # Reconstruct the dictionary
            result = {
                "league_id": rule.league_id,
                "league_name": rule.league_name,
                "scoring_type": rule.scoring_type,
                "roster_positions": json.loads(rule.roster_positions) if rule.roster_positions else [],
                "scoring_settings": json.loads(rule.scoring_settings) if rule.scoring_settings else {},
                "position_eligibility": json.loads(rule.position_eligibility) if rule.position_eligibility else {},
                "num_teams": rule.num_teams,
                "season": rule.season,
                "raw_data": json.loads(rule.raw_data) if rule.raw_data else {},
                "discovered_at": rule.discovered_at.isoformat() if rule.discovered_at else None,
            }
            
            self._cache[league_id] = result
            return result
        except Exception as e:
            logger.error(f"Error retrieving league rules: {e}")
            return None
    
    def has_league_rules(self, league_id: str) -> bool:
        """Check if league rules exist for the given ID.
        
        Args:
            league_id: League identifier
            
        Returns:
            True if rules exist
        """
        return self.get_league_rules(league_id) is not None
    
    def get_all_leagues(self) -> Dict[str, Dict[str, Any]]:
        """Get all stored league rules.
        
        Returns:
            Dictionary mapping league IDs to their rules
        """
        try:
            rules = self._session.query(LeagueRule).all()
            result = {}
            for rule in rules:
                result[rule.league_id] = {
                    "league_id": rule.league_id,
                    "league_name": rule.league_name,
                    "scoring_type": rule.scoring_type,
                    "roster_positions": json.loads(rule.roster_positions) if rule.roster_positions else [],
                    "scoring_settings": json.loads(rule.scoring_settings) if rule.scoring_settings else {},
                    "position_eligibility": json.loads(rule.position_eligibility) if rule.position_eligibility else {},
                    "num_teams": rule.num_teams,
                    "season": rule.season,
                    "raw_data": json.loads(rule.raw_data) if rule.raw_data else {},
                    "discovered_at": rule.discovered_at.isoformat() if rule.discovered_at else None,
                }
            return result
        except Exception as e:
            logger.error(f"Error retrieving all leagues: {e}")
            return {}
    
    def clear_league_rules(self, league_id: Optional[str] = None) -> None:
        """Clear league rules from database.
        
        Args:
            league_id: Specific league to clear, or None to clear all
        """
        try:
            if league_id:
                self._session.query(LeagueRule).filter_by(league_id=league_id).delete()
                self._cache.pop(league_id, None)
            else:
                self._session.query(LeagueRule).delete()
                self._cache.clear()
            self._session.commit()
            logger.info(f"Cleared league rules for {league_id if league_id else 'all leagues'}")
        except Exception as e:
            logger.error(f"Error clearing league rules: {e}")
            self._session.rollback()
    
    def format_rules_for_agent(self, league_id: str) -> str:
        """Format league rules as a string for agent context.
        
        Args:
            league_id: League identifier
            
        Returns:
            Formatted string with league rules
        """
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
        """Search for leagues matching a query.
        
        Args:
            query: Search query
            
        Returns:
            List of matching league rules
        """
        query_lower = query.lower()
        results = []
        all_leagues = self.get_all_leagues()
        for league_data in all_leagues.values():
            if query_lower in json.dumps(league_data).lower():
                results.append(league_data)
        return results
