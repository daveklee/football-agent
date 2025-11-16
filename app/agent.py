"""Main Fantasy Football Agent using Google ADK."""
import asyncio
import logging
from typing import List, Dict, Any, Optional

# Try different import patterns for Google ADK
try:
    from google.adk.agents import Agent
    from google.adk.tools.google_search_tool import GoogleSearchTool
    GoogleSearch = GoogleSearchTool
    ADK_IMPORT_STYLE = "new"
except ImportError:
    try:
        from google.adk import Agent
        from google.adk.tools.google_search_tool import GoogleSearchTool
        GoogleSearch = GoogleSearchTool
        ADK_IMPORT_STYLE = "old"
    except ImportError:
        # Fallback: create minimal Agent class if ADK not available
        class Agent:
            def __init__(self, **kwargs):
                self.name = kwargs.get('name', 'agent')
                self.model = kwargs.get('model', 'gemini-2.5-pro')
                self.tools = kwargs.get('tools', [])
                self.instruction = kwargs.get('instruction', '')
        GoogleSearch = None
        ADK_IMPORT_STYLE = "fallback"
        logging.warning("Google ADK not found. Using fallback implementation.")

import google.generativeai as genai

from app.utils.config import settings
from app.utils.tools.analysis_tools import AnalysisTools
from app.utils.league_memory import LeagueRulesMemory
from app.utils.tools.league_rules_tool import LeagueRulesTool

# Import MCP toolset support
try:
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Logger will be defined below

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.gemini_api_key)


class FantasyFootballAgent(Agent):
    """Main agent for managing Yahoo Fantasy Football team."""
    
    # Class-level initialization to ensure _league_id exists before any method calls
    _league_id: Optional[str] = None
    
    def __init__(self):
        # Initialize league ID early (needed for _get_agent_instruction)
        # Use getattr to safely get from settings, defaulting to None
        try:
            self._league_id = settings.yahoo_league_id
        except (AttributeError, NameError):
            self._league_id = None
        
        # Initialize league rules memory for persistent storage
        self._league_memory = LeagueRulesMemory()
        
        # Initialize league rules tool for discovering and managing league settings
        league_rules_tool = LeagueRulesTool(memory=self._league_memory)
        
        # Initialize analysis tools (LLM-based)
        analysis_tools = AnalysisTools()
        
        # Collect all tools
        all_tools = [
            *analysis_tools.get_tools(),
            *league_rules_tool.get_tools(),
        ]
        
        # Add MCP toolsets if available
        if MCP_AVAILABLE:
            import os
            import json
            from dotenv import load_dotenv
            
            # Load environment variables from .env file
            project_root = os.path.dirname(os.path.dirname(__file__))
            env_path = os.path.join(project_root, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
            else:
                # Also try loading from current working directory
                load_dotenv()
            
            # Load MCP config - look in project root (where agent.py is: app/agent.py, so go up 2 levels)
            # Or use absolute path from current working directory
            mcp_config_path = os.path.join(os.getcwd(), 'mcp_config.json')
            if not os.path.exists(mcp_config_path):
                # Fallback: try relative to this file
                mcp_config_path = os.path.join(project_root, 'mcp_config.json')
            if os.path.exists(mcp_config_path):
                with open(mcp_config_path, 'r') as f:
                    mcp_config = json.load(f)
                
                # Add Yahoo Fantasy MCP server
                if 'yahoo-fantasy' in mcp_config.get('mcpServers', {}):
                    yahoo_config = mcp_config['mcpServers']['yahoo-fantasy']
                    
                    # Handle cwd - expand ${PWD} to current working directory
                    cwd = yahoo_config.get('cwd', os.getcwd())
                    if cwd == "${PWD}":
                        cwd = os.getcwd()
                    
                    # The Yahoo Fantasy MCP server imports from 'src' module, so it needs
                    # the script directory in PYTHONPATH or to run from that directory
                    script_name = yahoo_config.get('args', [])[0] if yahoo_config.get('args') else None
                    if script_name:
                        # Get absolute path to script and its directory
                        script_path = os.path.abspath(os.path.join(cwd, script_name))
                        script_dir = os.path.dirname(script_path)
                        
                        # Start with environment variables (prioritize env vars over config)
                        yahoo_env = {}
                        
                        # Process config env vars, expanding ${VAR} placeholders from environment
                        config_env = yahoo_config.get('env', {})
                        for key, value in config_env.items():
                            # Expand ${VAR} placeholders from environment variables
                            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                                env_var_name = value[2:-1]
                                # Get from environment, or keep placeholder if not found
                                env_value = os.environ.get(env_var_name)
                                if env_value is not None:
                                    yahoo_env[key] = env_value
                                else:
                                    logger.warning(f"Environment variable {env_var_name} not found, skipping {key}")
                            else:
                                # Use value from config only if not already in environment
                                if key not in os.environ:
                                    yahoo_env[key] = value
                        
                        # Ensure PYTHONPATH includes the script directory so 'src' imports work
                        existing_pythonpath = yahoo_env.get('PYTHONPATH', '')
                        if existing_pythonpath:
                            yahoo_env['PYTHONPATH'] = script_dir + os.pathsep + existing_pythonpath
                        else:
                            yahoo_env['PYTHONPATH'] = script_dir
                        
                        # Use absolute path to script
                        args = [script_path] + yahoo_config.get('args', [])[1:]
                    else:
                        args = yahoo_config.get('args', [])
                        yahoo_env = {}
                        
                        # Process config env vars, expanding ${VAR} placeholders
                        config_env = yahoo_config.get('env', {})
                        for key, value in config_env.items():
                            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                                env_var_name = value[2:-1]
                                env_value = os.environ.get(env_var_name)
                                if env_value is not None:
                                    yahoo_env[key] = env_value
                                else:
                                    logger.warning(f"Environment variable {env_var_name} not found, skipping {key}")
                            else:
                                if key not in os.environ:
                                    yahoo_env[key] = value
                    
                    # Merge with current environment (environment variables take precedence)
                    final_env = os.environ.copy()
                    final_env.update(yahoo_env)
                    
                    logger.info(f"Yahoo MCP: Script={script_path if script_name else 'N/A'}, PYTHONPATH={final_env.get('PYTHONPATH', 'N/A')[:100]}")
                    
                    # Create stdio connection params
                    yahoo_params = StdioServerParameters(
                        command=yahoo_config['command'],
                        args=args,
                        env=final_env
                    )
                    
                    # Use StdioConnectionParams
                    # Note: The server needs to stay running and communicate via stdin/stdout
                    yahoo_connection = StdioConnectionParams(
                        server_params=yahoo_params,
                        timeout=60.0  # Increased timeout for server startup
                    )
                    
                    try:
                        yahoo_toolset = McpToolset(
                            connection_params=yahoo_connection,
                            tool_name_prefix='yahoo_'
                        )
                        all_tools.append(yahoo_toolset)
                        logger.info("Yahoo Fantasy MCP toolset added successfully")
                    except Exception as e:
                        logger.error(f"Failed to create Yahoo Fantasy MCP toolset: {e}")
                        logger.error("Yahoo Fantasy MCP will not be available")
                        import traceback
                        logger.debug(traceback.format_exc())
                
                # Add Browser MCP server
                # Browser MCP uses a Chrome extension - make sure it's installed: https://browsermcp.io/install
                if 'browsermcp' in mcp_config.get('mcpServers', {}):
                    browser_config = mcp_config['mcpServers']['browsermcp']
                    
                    try:
                        browser_params = StdioServerParameters(
                            command=browser_config['command'],
                            args=browser_config.get('args', [])
                        )
                        
                        # Use StdioConnectionParams for consistency
                        browser_connection = StdioConnectionParams(
                            server_params=browser_params,
                            timeout=60.0  # Increased timeout for server startup
                        )
                        
                        browser_toolset = McpToolset(
                            connection_params=browser_connection,
                            tool_name_prefix='browser_'
                        )
                        all_tools.append(browser_toolset)
                        logger.info("Browser MCP toolset added successfully")
                        logger.info("⚠️  Make sure Browser MCP Chrome extension is installed: https://browsermcp.io/install")
                    except Exception as e:
                        logger.error(f"Browser MCP toolset failed to initialize: {e}")
                        logger.error("Browser MCP will not be available")
                        logger.info("Make sure:")
                        logger.info("  1. Browser MCP Chrome extension is installed: https://browsermcp.io/install")
                        logger.info("  2. Node.js is installed (for npx)")
                        logger.info("  3. Package @browsermcp/mcp is accessible via npx")
                        import traceback
                        logger.debug(traceback.format_exc())
            else:
                logger.warning(f"MCP config not found at {mcp_config_path}")
        else:
            logger.warning("MCP tools not available - using placeholder tools")
            # Fallback to placeholder tools if MCP not available
            from app.utils.tools.yahoo_tools import YahooFantasyTools
            from app.utils.tools.browser_tools import BrowserAutomationTools
            yahoo_tools = YahooFantasyTools()
            browser_tools = BrowserAutomationTools()
            all_tools.extend(yahoo_tools.get_tools())
            all_tools.extend(browser_tools.get_tools())
        
        # Note: Google Search tool removed - Gemini doesn't support mixing
        # custom FunctionTools with built-in tools like google_search.
        # If you need web search, use it via MCP or a separate agent.
        # if GoogleSearch:
        #     all_tools.append(GoogleSearch())
        
        # Initialize agent with tools (Pro supports function calling)
        # Explicitly create Gemini LLM instance to ensure model is set correctly
        # This prevents ADK from using defaults that might not support function calling
        if ADK_IMPORT_STYLE == "new":
            try:
                from google.adk.models.google_llm import Gemini
                # Create Gemini LLM instance explicitly to ensure model is set correctly
                # The default is gemini-2.5-flash, so we must explicitly set gemini-2.5-pro
                llm = Gemini(model=settings.model_name)
                logger.info(f"Initializing agent with explicit Gemini LLM model: {settings.model_name}")
                super().__init__(
                    model=llm,
                    name="fantasy_football_manager",
                    tools=all_tools,
                    instruction=self._get_agent_instruction()
                )
            except ImportError:
                # Fallback to string model name
                logger.warning("Could not import Gemini, using string model name")
                super().__init__(
                    model=settings.model_name,
                    name="fantasy_football_manager",
                    tools=all_tools,
                    instruction=self._get_agent_instruction()
                )
        elif ADK_IMPORT_STYLE == "old":
            super().__init__()
            self.name = "fantasy_football_manager"
            self.model = settings.model_name
            self.tools = all_tools
            self.instruction = self._get_agent_instruction()
        else:  # fallback
            super().__init__(
                name="fantasy_football_manager",
                model=settings.model_name,
                tools=all_tools,
                instruction=self._get_agent_instruction()
            )
        
        # Store tool instances for direct method calls
        self._analysis_tools = analysis_tools
        self._league_rules_tool = league_rules_tool
        # Note: Yahoo and Browser tools are now MCP toolsets, not direct instances
        # They're accessible via the agent's tools list
        
        # Try to load stored league rules if available
        if self._league_id:
            stored_rules = self._league_memory.get_league_rules(self._league_id)
            if stored_rules:
                logger.info(f"Loaded stored league rules for league {self._league_id}")
                logger.info(f"  Scoring: {stored_rules.get('scoring_type', 'Unknown')}")
            else:
                logger.info(f"No stored rules found for league {self._league_id} - agent will need to discover them")
    
    def _get_agent_instruction(self) -> str:
        """Get the main instruction for the agent."""
        # Include stored league rules in instructions if available
        league_rules_context = ""
        # Safely check if _league_id exists (may not be set during initialization)
        league_id = getattr(self, '_league_id', None)
        if league_id:
            stored_rules = self._league_memory.get_league_rules(league_id)
            if stored_rules:
                league_rules_context = self._league_memory.format_rules_for_agent(league_id)
                league_rules_context += "\n⚠️ These rules are stored in memory. Always use these when making decisions.\n"
            else:
                league_rules_context = "\n⚠️ IMPORTANT: League rules not yet discovered! You MUST discover them first.\n"
        
        return f"""
You are an expert Fantasy Football team manager agent. Your primary responsibilities include:

1. **Lineup Optimization**: Analyze matchups, player performance, injuries, and weather conditions to optimize the weekly lineup. CRITICALLY IMPORTANT: You MUST consider your league's unique scoring system, roster positions, and rules before making ANY lineup decisions.

2. **Waiver Wire Management**: Monitor available players on the waiver wire, evaluate their potential value, and make recommendations or execute pickups when beneficial. Consider roster needs, bye weeks, AND league-specific position requirements.

3. **Trade Evaluation**: Evaluate pending trade offers by analyzing player values, team needs, and long-term implications. Propose new trades when they would improve the team. Always consider how league scoring rules affect player values (e.g., PPR leagues favor pass-catching RBs and WRs).

4. **Player Research**: Always consult current data and news from the internet about each player and team before making decisions. Consider:
   - Recent performance trends
   - Injury reports and status
   - Matchup difficulty
   - Weather conditions
   - Team news and depth chart changes
   - Expert analysis and projections
   - How league scoring rules affect player value (e.g., PPR scoring makes receptions valuable)

5. **League Rules Compliance**: This is CRITICAL. You MUST:
   - ALWAYS fetch league rules using yahoo_ff_get_league_info BEFORE making any decisions
   - Respect the exact roster positions required (e.g., some leagues have 2 FLEX spots, some have SUPERFLEX, some have IDP positions)
   - Understand the scoring system (Standard, PPR, Half-PPR, custom scoring) and how it affects player values
   - Follow position eligibility rules (e.g., which positions can fill FLEX spots)
   - Respect roster limits and transaction rules
   - Never suggest lineups that violate position requirements

6. **Decision Making Process**:
   STEP 1: ALWAYS check if league rules are known:
     - First, call check_if_rules_known to see if rules are already stored in memory
     - If rules are NOT known, you MUST discover them completely:
       
       **A. Discover via Yahoo Fantasy API:**
       * Call yahoo_ff_get_league_info to get ACTUAL league settings from Yahoo Fantasy API
       * NEVER assume standard scoring or positions - every league is different!
       * The API response will include:
         - Scoring type (Standard, PPR, Half-PPR, or custom - discover the actual type!)
         - Roster positions (exact positions required - may be non-standard like 2 FLEX, SUPERFLEX, IDP, etc.)
         - Position eligibility rules (which positions can fill FLEX spots)
         - Basic scoring settings (if available via API)
       
       **B. Discover via Browser (CRITICAL for complete scoring rules):**
       * The Yahoo API may NOT expose all custom scoring rules
       * You MUST navigate to the league scoring details page to discover complete scoring rules:
         - Use browser_navigate to go to: https://football.fantasysports.yahoo.com/f1/<league_id>/settings
         - Or navigate to: https://football.fantasysports.yahoo.com/f1/<league_id>/settings?tab=scoring
         - Replace <league_id> with the actual league ID from your configuration
       * Use browser_snapshot to see the page structure
       * Look for scoring settings sections that show:
         - Points per reception (PPR) - may be 0, 0.5, or 1.0
         - Points per passing yard, rushing yard, receiving yard
         - Points per touchdown (passing, rushing, receiving)
         - Points per field goal (by distance)
         - Points per extra point
         - Defensive scoring (points allowed, sacks, interceptions, etc.)
         - Any custom scoring bonuses or penalties
         - Kicker scoring details
         - Defense/ST scoring details
       * Use browser_screenshot if needed to capture scoring details
       * Read all scoring categories carefully - there may be custom rules not in the API
       
       **C. Store Complete Rules:**
       * Combine API data with browser-discovered scoring details
       * Call discover_and_store_league_rules with the complete league_info including:
         - All scoring rules discovered from browser
         - Roster positions from API
         - Any other league settings
       * Store everything so you remember it for future use
       
     - If rules ARE known, use get_stored_league_rules to retrieve them
     - CRITICAL: Always use the discovered rules - never assume standard settings!
     - IMPORTANT: If you only have API data, you may be missing custom scoring rules - always check the browser!
   
   STEP 2: Gather current data:
     - Use yahoo_ff_get_roster to get your team data
     - Use yahoo_ff_get_matchup to get weekly matchup information
     - Use yahoo_ff_get_standings to see league standings
     - Use yahoo_ff_get_waiver_wire or yahoo_ff_get_players to find available players
   
   STEP 3: Analyze with league rules in mind:
     - Consider how scoring rules affect player values (PPR vs Standard)
     - Ensure lineup suggestions match exact position requirements
     - Use yahoo_ff_build_lineup for advanced lineup optimization (it respects league rules)
   
   STEP 4: Execute actions:
     - Use Browser MCP tools to make changes in Yahoo Fantasy Football interface
     - Always verify lineup changes match league position requirements
     - Always explain your reasoning before making changes
   
   STEP 5: Provide final response:
     - After all tool calls complete, synthesize the results
     - Provide a clear, human-readable summary to the user
     - Include what was discovered, what actions were taken (if any), and recommendations
     - Always conclude with a final response - never leave the user without an answer

7. **Communication**: 
   - Before making any significant changes (trades, drops, lineup changes), explain your reasoning and the expected impact, including how league scoring rules influenced your decision.
   - **CRITICAL**: After executing tool calls, ALWAYS provide a clear, human-readable summary response to the user.
   - After tool calls complete, synthesize the results and provide a final answer or summary.
   - Never leave the user without a response - always conclude with a summary of what was done or discovered.

{league_rules_context}

IMPORTANT RULES:
- ALWAYS check if league rules are known using check_if_rules_known FIRST
- If rules are NOT known, you MUST discover them COMPLETELY:
  * Use yahoo_ff_get_league_info for basic league settings (roster positions, etc.)
  * Use Browser MCP to navigate to league settings page for COMPLETE scoring rules
  * The Yahoo API may not expose all custom scoring - browser discovery is CRITICAL
- NEVER assume standard scoring or roster positions - every league is different
- After discovering rules, store them using discover_and_store_league_rules so you remember them
- Use get_stored_league_rules to retrieve previously discovered rules
- League rules are stored in memory - you don't need to fetch them every time once discovered
- When discovering scoring rules, check BOTH API and browser to ensure completeness
- PPR leagues (Points Per Reception) significantly favor pass-catching RBs and WRs
- Half-PPR leagues provide moderate boost to pass-catchers
- Standard scoring favors TD-dependent players
- Some leagues have SUPERFLEX (can start QB in FLEX) - this dramatically increases QB value
- Some leagues have IDP (Individual Defensive Players) - these require different strategies
- Position eligibility matters: FLEX typically allows RB/WR/TE, SUPERFLEX allows QB/RB/WR/TE
- Always verify the exact roster positions required before suggesting lineups
- Use Yahoo Fantasy MCP tools (prefixed with 'yahoo_') to get all fantasy football data
- Available Yahoo tools: yahoo_ff_get_leagues, yahoo_ff_get_league_info, yahoo_ff_get_roster, yahoo_ff_get_matchup, yahoo_ff_get_standings, yahoo_ff_get_teams, yahoo_ff_get_players, yahoo_ff_get_waiver_wire, yahoo_ff_build_lineup, yahoo_ff_compare_teams, and more
- League Rules Memory tools:
  - check_if_rules_known: Check if league rules are already stored in memory
  - discover_and_store_league_rules: Discover rules from Yahoo API and store them
  - get_stored_league_rules: Retrieve previously discovered and stored league rules
- Use Browser MCP tools (prefixed with 'browser_') to control the browser and make changes:
  - browser_navigate: Navigate to Yahoo Fantasy Football pages
  - browser_snapshot: See page structure and find elements
  - browser_click: Click buttons and elements
  - browser_type: Type text into forms
  - browser_drag_and_drop: Drag players to set lineup
  - browser_screenshot: Take screenshots for verification
  - browser_select_option: Select options from dropdowns
  - browser_press_key: Press keyboard keys (Enter, Escape, etc.)
  - browser_wait: Wait for page to load
  - browser_go_back/browser_go_forward: Navigate browser history
- Consider both short-term and long-term implications of decisions
- Be conservative with trades and drops - only make changes that clearly improve the team

**CRITICAL RESPONSE REQUIREMENTS:**
- After executing ANY tool calls, you MUST provide a final text response to the user
- Tool calls are intermediate steps - always conclude with a clear, human-readable summary
- Your final response should:
  * Synthesize all tool call results into a coherent answer
  * Explain what was discovered or accomplished
  * Provide recommendations or next steps
  * Be written in natural language, not just raw tool outputs
- Never end a conversation after tool calls without providing a summary response
- The warnings about "non-text parts" are normal when using function calling - ignore them and provide your final response anyway
"""
    
    async def fetch_league_rules(self, league_id: Optional[str] = None) -> Dict[str, Any]:
        """Get stored league rules from memory.
        
        This method retrieves previously discovered and stored league rules.
        To discover new rules, the agent should use the discover_and_store_league_rules tool.
        
        Args:
            league_id: League ID to fetch rules for. Defaults to configured league ID.
            
        Returns:
            Stored league rules if available, or empty dict if not found
        """
        league_id = league_id or getattr(self, '_league_id', None)
        
        if not league_id:
            logger.warning("No league ID available - cannot fetch league rules")
            return {}
        
        rules = self._league_memory.get_league_rules(league_id)
        if rules:
            logger.info(f"Retrieved stored league rules for league {league_id}")
            return rules
        else:
            logger.info(f"No stored rules found for league {league_id}")
            return {}
    
    async def optimize_lineup(self, week: Optional[int] = None) -> Dict[str, Any]:
        """Optimize the lineup for a given week.
        
        Note: This method now relies on the agent's MCP tools being called
        by the LLM directly. The agent will use Yahoo Fantasy MCP tools
        to get data and Browser MCP tools to make changes.
        
        CRITICAL: The agent MUST fetch league rules first using yahoo_ff_get_league_info
        to ensure lineup decisions respect league-specific scoring and position requirements.
        """
        logger.info(f"Optimizing lineup for week {week}")
        logger.info("IMPORTANT: Agent must fetch league rules first using yahoo_ff_get_league_info")
        logger.info("Note: Agent will use MCP tools directly via LLM function calling")
        
        # Return a message indicating the agent should use its tools
        return {
            'message': 'CRITICAL: First ensure league rules are known. If not, discover them from BOTH API and browser. '
                      'Then use yahoo_ff_get_roster and yahoo_ff_get_matchup to get team data. '
                      'Ensure your lineup suggestions match the exact position requirements and scoring rules. '
                      'Use yahoo_ff_build_lineup for advanced optimization that respects league rules. '
                      'Finally, use Browser MCP tools to make lineup changes.',
            'week': week,
            'note': 'MCP tools are available and will be called by the LLM automatically',
            'required_steps': [
                '1. Check if league rules are known using check_if_rules_known',
                '2. If not known:',
                '   a. Call yahoo_ff_get_league_info for basic settings',
                '   b. Navigate to league settings page via browser for COMPLETE scoring rules',
                '   c. Store complete rules using discover_and_store_league_rules',
                '3. Get stored league rules using get_stored_league_rules',
                '4. Call yahoo_ff_get_roster to get current team',
                '5. Call yahoo_ff_get_matchup to get weekly matchup',
                '6. Analyze with league rules in mind (PPR vs Standard, position requirements, custom scoring)',
                '7. Use yahoo_ff_build_lineup for optimal lineup respecting league rules',
                '8. Use Browser MCP tools to execute changes'
            ],
            'important': 'The Yahoo API may not expose all custom scoring rules - always check the browser settings page!'
        }
    
    async def evaluate_waiver_wire(self) -> Dict[str, Any]:
        """Evaluate and manage waiver wire pickups.
        
        Note: Agent will use Yahoo Fantasy MCP tools (yahoo_ff_get_waiver_wire, etc.)
        and Browser MCP tools to execute pickups.
        
        CRITICAL: The agent MUST consider league scoring rules when evaluating players.
        For example, in PPR leagues, pass-catching RBs and WRs are more valuable.
        """
        logger.info("Evaluating waiver wire")
        logger.info("IMPORTANT: Agent must consider league scoring rules (PPR vs Standard)")
        logger.info("Note: Agent will use MCP tools directly via LLM function calling")
        
        return {
            'message': 'CRITICAL: First call yahoo_ff_get_league_info to understand scoring rules. '
                      'In PPR leagues, prioritize pass-catching RBs and WRs. '
                      'In Standard leagues, prioritize TD-dependent players. '
                      'Use yahoo_ff_get_waiver_wire or yahoo_ff_get_players to find available players. '
                      'Consider your roster needs based on league position requirements. '
                      'Then use Browser MCP tools to add/drop players.',
            'note': 'MCP tools are available and will be called by the LLM automatically',
            'scoring_considerations': {
                'PPR': 'Prioritize players with high reception counts (slot WRs, pass-catching RBs)',
                'Half-PPR': 'Moderate boost to pass-catchers',
                'Standard': 'Prioritize TD-dependent players and goal-line RBs'
            }
        }
    
    async def evaluate_trades(self) -> Dict[str, Any]:
        """Evaluate pending trades and propose new ones.
        
        Note: Agent will use Yahoo Fantasy MCP tools and Browser MCP tools
        to evaluate and execute trades.
        
        CRITICAL: The agent MUST consider league scoring rules when evaluating player values.
        Player values differ significantly between PPR and Standard leagues.
        """
        logger.info("Evaluating trades")
        logger.info("IMPORTANT: Agent must consider league scoring rules when valuing players")
        logger.info("Note: Agent will use MCP tools directly via LLM function calling")
        
        return {
            'message': 'CRITICAL: First call yahoo_ff_get_league_info to understand scoring rules. '
                      'Player values differ significantly between PPR and Standard leagues. '
                      'In PPR: Pass-catching RBs and WRs are more valuable. '
                      'In Standard: TD-dependent players are more valuable. '
                      'Use Yahoo Fantasy MCP tools to get trade information and compare teams. '
                      'Then use Browser MCP tools to propose/accept/reject trades.',
            'note': 'MCP tools are available and will be called by the LLM automatically',
            'scoring_considerations': {
                'PPR': 'Pass-catching players have higher value',
                'Standard': 'TD-dependent players have higher value'
            }
        }
    
    async def _research_players(self, players: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Research players using web search."""
        research_results = {}
        
        for player in players:
            player_name = player.get('name', '')
            team = player.get('team', '')
            
            # Search for latest news and stats
            search_query = f"{player_name} {team} fantasy football 2024 news stats"
            # Use google_search tool here
            # This would be implemented with actual web search
            
            research_results[player.get('player_id')] = {
                'name': player_name,
                'recent_news': [],  # Would be populated by search
                'stats': {},  # Would be populated by search
            }
        
        return research_results
    
    async def run_weekly_management(self) -> Dict[str, Any]:
        """Run all weekly management tasks."""
        logger.info("Running weekly management tasks")
        
        results = {
            'lineup_optimization': await self.optimize_lineup(),
            'waiver_wire': await self.evaluate_waiver_wire(),
            'trades': await self.evaluate_trades(),
        }
        
        return results


# Create agent instance
agent = FantasyFootballAgent()

# ADK web UI expects 'root_agent' variable
root_agent = agent

