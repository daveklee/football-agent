"""Analysis tools using LLM for decision making."""
import logging
from typing import List, Dict, Any, Optional
from google.adk.tools import FunctionTool
import google.generativeai as genai

from app.utils.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.model_name)


class AnalysisTools:
    """Tools for LLM-based analysis and decision making."""
    
    def get_tools(self) -> List[FunctionTool]:
        """Get all analysis tools."""
        return [
            FunctionTool(func=self.optimize_lineup),
            FunctionTool(func=self.evaluate_waiver_wire),
            FunctionTool(func=self.evaluate_trade),
            FunctionTool(func=self.propose_trades),
        ]
    
    async def optimize_lineup(
        self,
        team_data: Dict[str, Any],
        league_settings: Dict[str, Any],
        matchup: Dict[str, Any],
        player_research: Dict[str, Any],
        week: int
    ) -> Dict[str, Any]:
        """Optimize lineup using LLM analysis."""
        try:
            prompt = f"""
You are analyzing a Fantasy Football lineup for Week {week}.

TEAM DATA:
{self._format_team_data(team_data)}

LEAGUE SETTINGS:
{self._format_league_settings(league_settings)}

MATCHUP:
Opponent: {matchup.get('opponent', 'TBD')}
Current Score: {matchup.get('my_score', 0)} vs {matchup.get('opponent_score', 0)}

PLAYER RESEARCH:
{self._format_player_research(player_research)}

Based on this information, analyze the optimal lineup considering:
1. Matchup difficulty for each player
2. Recent performance trends
3. Injury status and game-time decisions
4. Weather conditions
5. Team news and depth chart changes
6. League-specific scoring rules

Provide:
1. Recommended starting lineup with reasoning
2. Players to bench with reasoning
3. Any position swaps needed
4. Confidence level for each decision

Format your response as JSON with the following structure:
{{
    "recommended_changes": [
        {{
            "player_id": "...",
            "action": "start|bench|move",
            "position": "...",
            "reasoning": "..."
        }}
    ],
    "changes_needed": true/false,
    "confidence": 0.0-1.0,
    "summary": "..."
}}
"""
            
            response = model.generate_content(prompt)
            result = self._parse_llm_response(response.text)
            
            return result
        except Exception as e:
            logger.error(f"Error optimizing lineup: {e}")
            return {'error': str(e), 'changes_needed': False}
    
    async def evaluate_waiver_wire(
        self,
        available_players: List[Dict[str, Any]],
        team_data: Dict[str, Any],
        league_settings: Dict[str, Any],
        player_research: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate waiver wire players."""
        try:
            prompt = f"""
You are evaluating waiver wire players for a Fantasy Football team.

CURRENT TEAM:
{self._format_team_data(team_data)}

LEAGUE SETTINGS:
{self._format_league_settings(league_settings)}

AVAILABLE PLAYERS (Top 20):
{self._format_available_players(available_players[:20])}

PLAYER RESEARCH:
{self._format_player_research(player_research)}

Analyze which players, if any, should be picked up. Consider:
1. Team needs (positions, bye weeks, injuries)
2. Player potential and recent performance
3. Long-term vs short-term value
4. Who to drop if picking up a player

Provide recommendations in JSON format:
{{
    "should_pickup": true/false,
    "player_id": "...",
    "drop_player_id": "...",
    "reasoning": "...",
    "priority": "high|medium|low"
}}
"""
            
            response = model.generate_content(prompt)
            result = self._parse_llm_response(response.text)
            
            return result
        except Exception as e:
            logger.error(f"Error evaluating waiver wire: {e}")
            return {'should_pickup': False, 'error': str(e)}
    
    async def evaluate_trade(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a trade offer."""
        try:
            prompt = f"""
You are evaluating a Fantasy Football trade offer.

TRADE DETAILS:
{self._format_trade(trade)}

Analyze this trade considering:
1. Player values and projections
2. Team needs
3. Long-term implications
4. League context

Provide evaluation in JSON format:
{{
    "should_accept": true/false,
    "reasoning": "...",
    "value_difference": "favorable|neutral|unfavorable",
    "confidence": 0.0-1.0
}}
"""
            
            response = model.generate_content(prompt)
            result = self._parse_llm_response(response.text)
            
            return result
        except Exception as e:
            logger.error(f"Error evaluating trade: {e}")
            return {'should_accept': False, 'error': str(e)}
    
    async def propose_trades(
        self,
        team_data: Dict[str, Any],
        league_settings: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Propose beneficial trades."""
        try:
            prompt = f"""
You are proposing Fantasy Football trades.

CURRENT TEAM:
{self._format_team_data(team_data)}

LEAGUE SETTINGS:
{self._format_league_settings(league_settings)}

Analyze the team and propose 1-3 trades that would improve the team. Consider:
1. Team weaknesses
2. Position depth
3. Player values
4. Trade feasibility

Provide proposals in JSON format:
{{
    "proposed_trades": [
        {{
            "target_team": "...",
            "players_to_give": ["player_id1", "player_id2"],
            "players_to_receive": ["player_id3", "player_id4"],
            "reasoning": "...",
            "priority": "high|medium|low"
        }}
    ]
}}
"""
            
            response = model.generate_content(prompt)
            result = self._parse_llm_response(response.text)
            
            return result.get('proposed_trades', [])
        except Exception as e:
            logger.error(f"Error proposing trades: {e}")
            return []
    
    def _format_team_data(self, team_data: Dict[str, Any]) -> str:
        """Format team data for LLM prompt."""
        roster = team_data.get('roster', [])
        formatted = f"Team: {team_data.get('team_name', 'Unknown')}\n"
        formatted += f"Record: {team_data.get('record', {})}\n\n"
        formatted += "Roster:\n"
        for player in roster:
            formatted += f"  - {player.get('name')} ({player.get('position')}) - {player.get('team')} - {player.get('status')}\n"
        return formatted
    
    def _format_league_settings(self, settings: Dict[str, Any]) -> str:
        """Format league settings for LLM prompt."""
        formatted = f"Scoring Type: {settings.get('scoring_type', 'Unknown')}\n"
        formatted += "Roster Positions:\n"
        for pos, count in settings.get('roster_positions', {}).items():
            formatted += f"  - {pos}: {count}\n"
        return formatted
    
    def _format_player_research(self, research: Dict[str, Any]) -> str:
        """Format player research for LLM prompt."""
        formatted = ""
        for player_id, data in research.items():
            formatted += f"{data.get('name', 'Unknown')}:\n"
            formatted += f"  News: {', '.join(data.get('recent_news', []))}\n"
            formatted += f"  Stats: {data.get('stats', {})}\n"
        return formatted
    
    def _format_available_players(self, players: List[Dict[str, Any]]) -> str:
        """Format available players for LLM prompt."""
        formatted = ""
        for player in players:
            formatted += f"  - {player.get('name')} ({player.get('position')}) - {player.get('team')}\n"
        return formatted
    
    def _format_trade(self, trade: Dict[str, Any]) -> str:
        """Format trade details for LLM prompt."""
        formatted = f"Trade ID: {trade.get('trade_id')}\n"
        formatted += f"From: {trade.get('from_team')}\n"
        formatted += f"To: {trade.get('to_team')}\n"
        formatted += f"Players Offered: {trade.get('players_offered', [])}\n"
        formatted += f"Players Requested: {trade.get('players_requested', [])}\n"
        return formatted
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response, attempting to extract JSON."""
        import json
        import re
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # If JSON parsing fails, return the raw response
        return {'raw_response': response_text}

