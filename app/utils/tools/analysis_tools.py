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

⚠️ CRITICAL: You MUST use the league settings below - NEVER make generic recommendations!

TEAM DATA:
{self._format_team_data(team_data)}

LEAGUE SETTINGS (USE THESE EXACT RULES - DO NOT ASSUME STANDARD SETTINGS):
{self._format_league_settings(league_settings)}

MATCHUP:
Opponent: {matchup.get('opponent', 'TBD')}
Current Score: {matchup.get('my_score', 0)} vs {matchup.get('opponent_score', 0)}

PLAYER RESEARCH:
{self._format_player_research(player_research)}

Based on this information, analyze the optimal lineup considering:
1. **CRITICAL**: Use the EXACT league-specific scoring rules from above (PPR vs Standard significantly affects player values)
   - If PPR: Prioritize players with high reception counts
   - If Standard: Prioritize TD-dependent players
   - Use the scoring_settings from league_settings to calculate player values accurately
2. **CRITICAL**: Match EXACT roster position requirements from league_settings - lineup MUST match positions exactly
   - Check roster_positions from league_settings
   - Ensure you're filling ALL required positions (e.g., if 2 FLEX spots, fill both)
   - Use position_eligibility from league_settings to determine which players can fill FLEX/SUPERFLEX spots
3. Matchup difficulty for each player
4. Recent performance trends:
   - In PPR leagues: Prioritize receptions heavily
   - In Standard leagues: Prioritize touchdowns and yards
   - Use the scoring format from league_settings to weight stats correctly
5. Injury status and game-time decisions
6. Weather conditions
7. Team news and depth chart changes
8. Position eligibility rules from league_settings (which positions can fill FLEX/SUPERFLEX spots)

⚠️ IMPORTANT: In your reasoning, explicitly state which league rules you're using (e.g., "In this PPR league..." or "Given the SUPERFLEX position...")

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

⚠️ CRITICAL: You MUST use the league settings below - NEVER make generic recommendations!

CURRENT TEAM:
{self._format_team_data(team_data)}

LEAGUE SETTINGS (USE THESE EXACT RULES - DO NOT ASSUME STANDARD SETTINGS):
{self._format_league_settings(league_settings)}

AVAILABLE PLAYERS (Top 20):
{self._format_available_players(available_players[:20])}

PLAYER RESEARCH:
{self._format_player_research(player_research)}

Analyze which players, if any, should be picked up. Consider:
1. **CRITICAL**: Use the EXACT league scoring rules from above:
   - If PPR league: Prioritize pass-catching players (high reception counts)
   - If Standard league: Prioritize TD-dependent players
   - Use scoring_settings from league_settings to calculate accurate player values
   - Example: In PPR, a WR with 8 catches for 60 yards = 14 points vs 6 points in Standard
2. **CRITICAL**: Match league position requirements from league_settings:
   - Check roster_positions to see exact position needs
   - Ensure recommendations fit YOUR league's structure (e.g., SUPERFLEX, 2 FLEX, IDP)
   - Use position_eligibility to determine which players can fill FLEX spots
3. Team needs (positions, bye weeks, injuries) based on YOUR league's position requirements
4. Player potential and recent performance:
   - In PPR leagues: Weight receptions heavily in evaluation
   - In Standard leagues: Weight touchdowns and yards heavily
   - Use the scoring format from league_settings to evaluate correctly
5. Long-term vs short-term value based on YOUR league's scoring system
6. Who to drop if picking up a player (consider YOUR league's position needs)
7. How YOUR league's specific scoring rules affect player values

⚠️ IMPORTANT: In your reasoning, explicitly reference which league rules you're using (e.g., "In this PPR league, Player X is valuable because..." or "Given the SUPERFLEX position...")

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
    
    async def evaluate_trade(
        self, 
        trade: Dict[str, Any],
        league_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Evaluate a trade offer."""
        try:
            league_context = ""
            if league_settings:
                league_context = f"\nLEAGUE SETTINGS (USE THESE EXACT RULES):\n{self._format_league_settings(league_settings)}\n"
            
            prompt = f"""
You are evaluating a Fantasy Football trade offer.

⚠️ CRITICAL: You MUST use the league settings below - NEVER make generic trade evaluations!

TRADE DETAILS:
{self._format_trade(trade)}
{league_context}

Analyze this trade considering:
1. **CRITICAL**: Player values based on YOUR league's scoring rules:
   - If PPR league: Pass-catching players are MORE valuable
   - If Standard league: TD-dependent players are MORE valuable
   - If SUPERFLEX/2QB league: QBs are MUCH more valuable
   - Use scoring_settings from league_settings to calculate accurate values
2. Team needs based on YOUR league's position requirements (check roster_positions)
3. Long-term implications considering YOUR league's scoring system
4. League context: Use position_eligibility to understand FLEX/SUPERFLEX value

⚠️ IMPORTANT: In your reasoning, explicitly state which league rules affect the trade (e.g., "In this PPR league, Player X's receptions make them more valuable..." or "Given the SUPERFLEX position, QB Y is worth...")

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

⚠️ CRITICAL: You MUST use the league settings below - NEVER make generic trade proposals!

CURRENT TEAM:
{self._format_team_data(team_data)}

LEAGUE SETTINGS (USE THESE EXACT RULES - DO NOT ASSUME STANDARD SETTINGS):
{self._format_league_settings(league_settings)}

Analyze the team and propose 1-3 trades that would improve the team. Consider:
1. **CRITICAL**: Team weaknesses based on YOUR league's exact position requirements (check roster_positions):
   - If SUPERFLEX/2QB: Consider QB depth needs
   - If 2 FLEX spots: Consider depth needs
   - Use position_eligibility to understand which players can fill FLEX spots
2. **CRITICAL**: Player values based on YOUR league's scoring rules:
   - If PPR league: Pass-catching players are MORE valuable in trades
   - If Standard league: TD-dependent players are MORE valuable
   - If SUPERFLEX/2QB: QBs are MUCH more valuable - factor this heavily
   - Use scoring_settings to calculate accurate trade values
3. Position depth based on YOUR league's position requirements
4. Long-term vs short-term value considering YOUR league's scoring system
5. Trade feasibility and fairness (consider YOUR league's scoring when evaluating fairness)

⚠️ IMPORTANT: In your reasoning, explicitly reference which league rules make the trade beneficial (e.g., "In this PPR league..." or "Given the SUPERFLEX position...")

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
        """Format league settings for LLM prompt with detailed scoring implications."""
        formatted = ""
        
        # Scoring type with implications
        scoring_type = settings.get('scoring_type', 'Unknown')
        formatted += f"Scoring Type: {scoring_type}\n"
        
        # Add scoring implications
        scoring_lower = scoring_type.lower()
        if 'ppr' in scoring_lower:
            formatted += "  ⚠️ CRITICAL: This is a PPR (Points Per Reception) league!\n"
            formatted += "  → Pass-catching RBs and WRs are SIGNIFICANTLY more valuable\n"
            formatted += "  → Prioritize players with high reception counts (slot receivers, pass-catching RBs)\n"
            formatted += "  → Example: A RB with 5 catches for 30 yards = 8 points in PPR vs 3 points in Standard\n"
        elif 'half' in scoring_lower or '0.5' in scoring_lower:
            formatted += "  ⚠️ IMPORTANT: This is a Half-PPR league\n"
            formatted += "  → Pass-catchers get moderate boost (0.5 points per reception)\n"
            formatted += "  → Balance between PPR and Standard strategies\n"
        else:
            formatted += "  → This is Standard scoring (no PPR)\n"
            formatted += "  → TD-dependent players are more valuable\n"
            formatted += "  → Goal-line RBs and red-zone targets are prioritized\n"
        
        # Roster positions with detailed breakdown
        roster_positions = settings.get('roster_positions', {})
        if roster_positions:
            formatted += "\nRoster Positions (CRITICAL - lineup must match exactly):\n"
            
            # Handle different formats
            if isinstance(roster_positions, dict):
                position_dict = roster_positions
            elif isinstance(roster_positions, list):
                # Convert list to dict
                position_dict = {}
                for pos in roster_positions:
                    if isinstance(pos, dict):
                        pos_name = pos.get('position', pos.get('type', 'Unknown'))
                        count = pos.get('count', 1)
                    else:
                        pos_name = str(pos)
                        count = 1
                    position_dict[pos_name] = position_dict.get(pos_name, 0) + count
            else:
                position_dict = {}
            
            # Separate starting positions from bench
            starting_positions = []
            bench_count = 0
            
            for pos, count in sorted(position_dict.items()):
                if pos.upper() in ['BN', 'BE', 'BENCH']:
                    bench_count += count
                elif pos.upper() not in ['IR', 'INJURED']:
                    starting_positions.append((pos, count))
            
            # Format starting positions
            for pos, count in starting_positions:
                formatted += f"  - {pos}: {count}\n"
                
                # Add position-specific notes
                if pos.upper() in ['SUPERFLEX', 'OP', 'OFFENSIVE PLAYER']:
                    formatted += "    ⚠️ SUPERFLEX allows QB in FLEX - QBs are MUCH more valuable!\n"
                elif pos.upper() == 'FLEX':
                    formatted += "    → FLEX typically allows RB/WR/TE - check exact eligibility\n"
                elif pos.upper() in ['IDP', 'IDP_FLEX']:
                    formatted += "    → IDP league - defensive players are required\n"
            
            if bench_count > 0:
                formatted += f"  - Bench: {bench_count} spots\n"
        
        # Custom scoring settings
        scoring_settings = settings.get('scoring_settings', {})
        if scoring_settings:
            formatted += "\nCustom Scoring Rules:\n"
            for key, value in scoring_settings.items():
                formatted += f"  - {key}: {value}\n"
                # Add implications for common custom rules
                if 'reception' in key.lower() or 'rec' in key.lower():
                    formatted += "    → This affects pass-catching player values\n"
                elif 'passing' in key.lower():
                    formatted += "    → This affects QB values\n"
        
        # Position eligibility (if available)
        position_eligibility = settings.get('position_eligibility', {})
        if position_eligibility:
            formatted += "\nPosition Eligibility Rules:\n"
            for pos, eligible in position_eligibility.items():
                formatted += f"  - {pos} can be filled by: {', '.join(eligible)}\n"
        
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

