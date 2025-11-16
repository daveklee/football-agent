"""Tool for discovering and managing league rules."""
import logging
from typing import Dict, Any, Optional
from google.adk.tools import FunctionTool

from app.utils.league_memory import LeagueRulesMemory

logger = logging.getLogger(__name__)


class LeagueRulesTool:
    """Tool for discovering, storing, and retrieving league-specific rules.
    
    This tool ensures the agent always discovers the actual league rules from Yahoo
    Fantasy API rather than assuming standard settings. It also manages persistent
    storage so rules don't need to be fetched every time.
    """
    
    def __init__(self, memory: Optional[LeagueRulesMemory] = None):
        """Initialize league rules tool.
        
        Args:
            memory: LeagueRulesMemory instance for persistent storage
        """
        self.memory = memory or LeagueRulesMemory()
    
    def get_tools(self) -> list[FunctionTool]:
        """Get all league rules management tools."""
        return [
            FunctionTool(func=self.discover_and_store_league_rules),
            FunctionTool(func=self.get_stored_league_rules),
            FunctionTool(func=self.check_if_rules_known),
        ]
    
    async def discover_and_store_league_rules(
        self,
        league_info: Optional[Dict[str, Any]] = None,
        league_id: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Discover league rules from Yahoo Fantasy API and store them for future use.
        
        This tool MUST be called to discover the actual league rules. Never assume
        standard scoring or roster positions - every league can be different!
        
        Usage:
        1. First call yahoo_ff_get_league_info to fetch league settings from Yahoo API
        2. Pass the league_info result to this tool to store it
        3. Future calls will use stored rules automatically
        
        Args:
            league_info: League information from yahoo_ff_get_league_info. If provided, stores it.
            league_id: Yahoo Fantasy league ID. If not provided, uses default from config or from league_info.
            force_refresh: If True, always fetch fresh rules even if stored.
            
        Returns:
            Dictionary with league rules and status
            
        Note:
            If league_info is not provided, returns instructions to fetch it first.
            The agent should call yahoo_ff_get_league_info first, then pass results here.
        """
        from app.utils.config import settings
        
        # Determine league_id
        if league_info and 'league_id' in league_info:
            league_id = league_id or league_info['league_id']
        league_id = league_id or settings.yahoo_league_id
        
        if not league_id:
            return {
                'status': 'error',
                'error': 'No league ID provided and no default league ID configured',
                'message': 'Please provide a league_id or set YAHOO_LEAGUE_ID in .env'
            }
        
        # If league_info is provided, store it
        if league_info:
            success = self.memory.store_league_rules(league_id, league_info)
            if success:
                stored_rules = self.memory.get_league_rules(league_id)
                return {
                    'status': 'success',
                    'source': 'discovered_and_stored',
                    'league_id': league_id,
                    'message': f'Successfully discovered and stored league rules for league {league_id}',
                    'rules': stored_rules,
                    'scoring_type': stored_rules.get('scoring_type', 'Unknown'),
                    'note': 'Rules are now stored in memory and will be remembered for future use.'
                }
            else:
                return {
                    'status': 'error',
                    'error': 'Failed to store league rules',
                    'league_id': league_id
                }
        
        # Check if rules are already stored
        if not force_refresh and self.memory.has_league_rules(league_id):
            stored_rules = self.memory.get_league_rules(league_id)
            return {
                'status': 'success',
                'source': 'stored',
                'league_id': league_id,
                'message': f'Using stored league rules for league {league_id}',
                'rules': stored_rules,
                'scoring_type': stored_rules.get('scoring_type', 'Unknown'),
                'note': 'Rules were previously discovered and stored. Use force_refresh=True to fetch fresh rules.'
            }
        
        # Rules need to be discovered - instruct agent to fetch them
        return {
            'status': 'needs_discovery',
            'league_id': league_id,
            'message': 'League rules need to be discovered from Yahoo Fantasy API AND browser',
            'instructions': [
                'STEP 1: Discover via Yahoo Fantasy API:',
                '  1. Call yahoo_ff_get_league_info with league_id to fetch ACTUAL league settings',
                '  2. The API response will include:',
                '     - scoring_type (Standard, PPR, Half-PPR, or custom - discover the actual type!)',
                '     - roster_positions (exact positions required - may be non-standard like 2 FLEX, SUPERFLEX, IDP, etc.)',
                '     - position_eligibility (which positions can fill FLEX spots)',
                '     - Basic scoring settings (if available via API)',
                '',
                'STEP 2: Discover COMPLETE scoring rules via Browser (CRITICAL!):',
                '  ⚠️ The Yahoo API may NOT expose all custom scoring rules!',
                '  ⚠️ You MUST navigate to the league settings page to get complete scoring details!',
                '  1. Use browser_navigate to go to:',
                f'     https://football.fantasysports.yahoo.com/f1/{league_id}/settings',
                '     OR',
                f'     https://football.fantasysports.yahoo.com/f1/{league_id}/settings?tab=scoring',
                '  2. Use browser_snapshot to see the page structure',
                '  3. Look for and read ALL scoring settings sections:',
                '     - Points per reception (PPR) - check if 0, 0.5, or 1.0',
                '     - Points per passing yard, rushing yard, receiving yard',
                '     - Points per touchdown (passing, rushing, receiving)',
                '     - Points per field goal (by distance)',
                '     - Points per extra point',
                '     - Defensive scoring (points allowed, sacks, interceptions, fumbles, etc.)',
                '     - Kicker scoring details',
                '     - Defense/ST scoring details',
                '     - Any custom scoring bonuses or penalties',
                '  4. Use browser_screenshot if needed to capture scoring details',
                '  5. Read ALL scoring categories - there may be custom rules not in the API',
                '',
                'STEP 3: Combine and Store:',
                '  1. Combine API data with browser-discovered scoring details',
                '  2. Create complete league_info object with ALL discovered rules',
                '  3. Call discover_and_store_league_rules(league_info=<complete_data>) to store it',
                '',
                'CRITICAL: Never assume standard settings - always discover the actual rules!',
                'CRITICAL: The API alone may be incomplete - always check the browser for full scoring rules!'
            ],
            'note': 'This league may have non-standard positions or scoring. Always discover the actual rules from BOTH API and browser.',
            'browser_url': f'https://football.fantasysports.yahoo.com/f1/{league_id}/settings?tab=scoring',
            'example': 'After calling yahoo_ff_get_league_info AND navigating to settings page, combine the data and call discover_and_store_league_rules(league_info=<combined_result>)'
        }
    
    async def get_stored_league_rules(self, league_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve stored league rules.
        
        Args:
            league_id: Yahoo Fantasy league ID. If not provided, uses default from config.
            
        Returns:
            Stored league rules if available, or instructions to discover them
        """
        from app.utils.config import settings
        
        league_id = league_id or settings.yahoo_league_id
        
        if not league_id:
            return {
                'status': 'error',
                'error': 'No league ID provided'
            }
        
        rules = self.memory.get_league_rules(league_id)
        
        if rules:
            return {
                'status': 'success',
                'league_id': league_id,
                'rules': rules,
                'formatted': self.memory.format_rules_for_agent(league_id)
            }
        else:
            return {
                'status': 'not_found',
                'league_id': league_id,
                'message': 'No stored rules found. Use discover_and_store_league_rules to discover them.',
                'instructions': 'Call discover_and_store_league_rules first to fetch and store league rules from Yahoo Fantasy API'
            }
    
    async def check_if_rules_known(self, league_id: Optional[str] = None) -> Dict[str, Any]:
        """Check if league rules are already known/stored.
        
        Args:
            league_id: Yahoo Fantasy league ID. If not provided, uses default from config.
            
        Returns:
            Status indicating whether rules are known
        """
        from app.utils.config import settings
        
        league_id = league_id or settings.yahoo_league_id
        
        if not league_id:
            return {
                'status': 'error',
                'error': 'No league ID provided'
            }
        
        is_known = self.memory.has_league_rules(league_id)
        
        if is_known:
            rules = self.memory.get_league_rules(league_id)
            return {
                'status': 'known',
                'league_id': league_id,
                'rules_known': True,
                'scoring_type': rules.get('scoring_type', 'Unknown'),
                'message': f'League rules are stored. Scoring: {rules.get("scoring_type", "Unknown")}'
            }
        else:
            return {
                'status': 'unknown',
                'league_id': league_id,
                'rules_known': False,
                'message': 'League rules not yet discovered. Call discover_and_store_league_rules to discover them.',
                'critical': 'NEVER assume standard scoring or positions - always discover the actual rules!'
            }

