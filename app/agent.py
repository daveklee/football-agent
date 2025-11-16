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

# Import MCP toolset support
try:
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP tools not available. Install mcp package: pip install mcp")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.gemini_api_key)


class FantasyFootballAgent(Agent):
    """Main agent for managing Yahoo Fantasy Football team."""
    
    def __init__(self):
        # Initialize analysis tools (LLM-based)
        analysis_tools = AnalysisTools()
        
        # Collect all tools
        all_tools = [
            *analysis_tools.get_tools(),
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
        # Note: Yahoo and Browser tools are now MCP toolsets, not direct instances
        # They're accessible via the agent's tools list
    
    def _get_agent_instruction(self) -> str:
        """Get the main instruction for the agent."""
        return """
You are an expert Fantasy Football team manager agent. Your primary responsibilities include:

1. **Lineup Optimization**: Analyze matchups, player performance, injuries, and weather conditions to optimize the weekly lineup. Always consider your league's unique scoring system and rules.

2. **Waiver Wire Management**: Monitor available players on the waiver wire, evaluate their potential value, and make recommendations or execute pickups when beneficial. Consider roster needs and bye weeks.

3. **Trade Evaluation**: Evaluate pending trade offers by analyzing player values, team needs, and long-term implications. Propose new trades when they would improve the team.

4. **Player Research**: Always consult current data and news from the internet about each player and team before making decisions. Consider:
   - Recent performance trends
   - Injury reports and status
   - Matchup difficulty
   - Weather conditions
   - Team news and depth chart changes
   - Expert analysis and projections

5. **League Rules Compliance**: Always respect your league's unique scoring system, roster limits, transaction rules, and any other custom settings.

6. **Decision Making Process**:
   - Gather current data from Yahoo Fantasy Football using Yahoo Fantasy MCP tools (prefixed with 'yahoo_')
     - Use yahoo_ff_get_roster to get your team data
     - Use yahoo_ff_get_league_info to get league settings
     - Use yahoo_ff_get_matchup to get weekly matchup information
     - Use yahoo_ff_get_standings to see league standings
     - Use yahoo_ff_get_waiver_wire or yahoo_ff_get_players to find available players
     - Use yahoo_ff_build_lineup for advanced lineup optimization
   - Research players using available tools and data sources for latest news and stats
   - Analyze using LLM reasoning
   - Execute actions using Browser MCP tools to make changes in Yahoo Fantasy Football interface
   - Always explain your reasoning before making changes

7. **Communication**: Before making any significant changes (trades, drops, lineup changes), explain your reasoning and the expected impact.

IMPORTANT: 
- Always verify league rules before making decisions using yahoo_ff_get_league_info
- Never make changes without understanding the full context
- Use Yahoo Fantasy MCP tools (prefixed with 'yahoo_') to get all fantasy football data
- Available Yahoo tools: yahoo_ff_get_leagues, yahoo_ff_get_league_info, yahoo_ff_get_roster, yahoo_ff_get_matchup, yahoo_ff_get_standings, yahoo_ff_get_teams, yahoo_ff_get_players, yahoo_ff_get_waiver_wire, yahoo_ff_build_lineup, yahoo_ff_compare_teams, and more
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
"""
    
    async def optimize_lineup(self, week: Optional[int] = None) -> Dict[str, Any]:
        """Optimize the lineup for a given week.
        
        Note: This method now relies on the agent's MCP tools being called
        by the LLM directly. The agent will use Yahoo Fantasy MCP tools
        to get data and Browser MCP tools to make changes.
        """
        logger.info(f"Optimizing lineup for week {week}")
        logger.info("Note: Agent will use MCP tools directly via LLM function calling")
        
        # Return a message indicating the agent should use its tools
        return {
            'message': 'Use your Yahoo Fantasy MCP tools (yahoo_ff_get_roster, yahoo_ff_get_matchup, etc.) '
                      'to get team data, then use Browser MCP tools to make lineup changes.',
            'week': week,
            'note': 'MCP tools are available and will be called by the LLM automatically'
        }
    
    async def evaluate_waiver_wire(self) -> Dict[str, Any]:
        """Evaluate and manage waiver wire pickups.
        
        Note: Agent will use Yahoo Fantasy MCP tools (yahoo_ff_get_waiver_wire, etc.)
        and Browser MCP tools to execute pickups.
        """
        logger.info("Evaluating waiver wire")
        logger.info("Note: Agent will use MCP tools directly via LLM function calling")
        
        return {
            'message': 'Use your Yahoo Fantasy MCP tools (yahoo_ff_get_waiver_wire, yahoo_ff_get_players) '
                      'to find available players, then use Browser MCP tools to add/drop players.',
            'note': 'MCP tools are available and will be called by the LLM automatically'
        }
    
    async def evaluate_trades(self) -> Dict[str, Any]:
        """Evaluate pending trades and propose new ones.
        
        Note: Agent will use Yahoo Fantasy MCP tools and Browser MCP tools
        to evaluate and execute trades.
        """
        logger.info("Evaluating trades")
        logger.info("Note: Agent will use MCP tools directly via LLM function calling")
        
        return {
            'message': 'Use your Yahoo Fantasy MCP tools to get trade information, '
                      'then use Browser MCP tools to propose/accept/reject trades.',
            'note': 'MCP tools are available and will be called by the LLM automatically'
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

