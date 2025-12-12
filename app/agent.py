"""Main Fantasy Football Agent using Google ADK."""
import asyncio
import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    try:
        from google.adk.agents import CallbackContext
    except ImportError:
        CallbackContext = Any  # type: ignore

# Try different import patterns for Google ADK
try:
    from google.adk.agents import Agent
    try:
        from google.adk.agents import CallbackContext
        ADK_CALLBACKS_AVAILABLE = True
    except ImportError:
        # CallbackContext might not be available in all ADK versions
        CallbackContext = Any  # type: ignore
        ADK_CALLBACKS_AVAILABLE = False
    from google.adk.tools.google_search_tool import GoogleSearchTool
    GoogleSearch = GoogleSearchTool
    ADK_IMPORT_STYLE = "new"
except ImportError:
    try:
        from google.adk import Agent
        from google.adk.tools.google_search_tool import GoogleSearchTool
        GoogleSearch = GoogleSearchTool
        ADK_IMPORT_STYLE = "old"
        ADK_CALLBACKS_AVAILABLE = False  # Old style may not support callbacks
        CallbackContext = Any  # type: ignore
    except ImportError:
        # Fallback: create minimal Agent class if ADK not available
        class Agent:
            def __init__(self, **kwargs):
                self.name = kwargs.get('name', 'agent')
                self.model = kwargs.get('model', settings.model_name)
                self.tools = kwargs.get('tools', [])
                self.instruction = kwargs.get('instruction', '')
        GoogleSearch = None
        ADK_IMPORT_STYLE = "fallback"
        ADK_CALLBACKS_AVAILABLE = False
        CallbackContext = Any  # type: ignore
        logging.warning("Google ADK not found. Using fallback implementation.")

try:
    from google.adk.tools.agent_tool import AgentTool
    AGENT_TOOL_AVAILABLE = True
except ImportError:
    AGENT_TOOL_AVAILABLE = False
    # logger not defined yet

from app.research_agent import ResearchAgent

import google.generativeai as genai

from app.utils.config import settings
from app.utils.tools.analysis_tools import AnalysisTools
from app.utils.database_league_memory import DatabaseLeagueRulesMemory
from app.utils.tools.league_rules_tool import LeagueRulesTool
from app.tools.memory_tools import remember_fact, get_all_facts, _fact_memory

# Context management imports for optimized prompts
from app.utils.prompts import build_agent_prompt, estimate_tokens

try:
    from google.adk.memory import InMemoryMemoryService
    from google.adk.memory.base_memory_service import BaseMemoryService

    ADK_MEMORY_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    InMemoryMemoryService = None  # type: ignore

    class BaseMemoryService:  # type: ignore
        ...

    ADK_MEMORY_AVAILABLE = False

DEFAULT_APP_NAME = "football-agent"
DEFAULT_MEMORY_SERVICE = InMemoryMemoryService() if ADK_MEMORY_AVAILABLE else None

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
genai.configure(api_key=settings.gemini_api_key, transport="rest")


class FantasyFootballAgent(Agent):
    """Main agent for managing Yahoo Fantasy Football team.
    
    This agent extends the base ADK Agent class, which automatically handles the
    Runner's event loop pattern. The agent's run_async method (inherited from
    base Agent) yields Events that the Runner processes according to the ADK
    Runtime event loop:
    
    1. Agent logic runs and yields Events
    2. Runner receives Events and commits state changes via Services
    3. Agent logic resumes after Runner processes the Events
    
    See: https://google.github.io/adk-docs/runtime/#execution-logics-role-agent-tool-callback
    """
    
    # Class-level initialization to ensure attributes exist before any method calls
    _league_id: Optional[str] = None
    _memory_service: Optional[BaseMemoryService] = None
    
    def __init__(self, memory_service: Optional[BaseMemoryService] = None):
        # Initialize memory service first (needed by LeagueRulesMemory)
        # Use provided memory_service, or fall back to default, or create a new one
        if memory_service is not None:
            self._memory_service = memory_service
        elif DEFAULT_MEMORY_SERVICE is not None:
            self._memory_service = DEFAULT_MEMORY_SERVICE
        elif ADK_MEMORY_AVAILABLE:
            # Create a new instance if ADK is available but no default was set
            self._memory_service = InMemoryMemoryService()
        else:
            # ADK memory not available - set to None (will be handled gracefully)
            self._memory_service = None
        
        # Initialize league ID early (needed for _get_agent_instruction)
        # Use getattr to safely get from settings, defaulting to None
        try:
            self._league_id = settings.yahoo_league_id
        except (AttributeError, NameError):
            self._league_id = None
        
        # Initialize league rules memory for persistent storage (database-backed)
        import os
        from pathlib import Path
        # Use project root for database path (consistent across runs)
        project_root = Path(__file__).parent.parent
        db_path = os.path.join(project_root, "sessions.db")
        db_url = f"sqlite:///{db_path}"
        self._league_memory = DatabaseLeagueRulesMemory(db_url=db_url)
        
        # Initialize league rules tool for discovering and managing league settings
        league_rules_tool = LeagueRulesTool(memory=self._league_memory)
        
        # Initialize analysis tools (LLM-based)
        analysis_tools = AnalysisTools()
        
        from app.utils.tools.yahoo_login_tool import YahooLoginTool
        yahoo_login_tool = YahooLoginTool()
        
        # Initialize projection extractor tool (for getting accurate projections from Yahoo website)
        from app.utils.tools.projection_extractor import ProjectionExtractorTool
        projection_tool = ProjectionExtractorTool()
        
        # Collect all tools
        all_tools = [
            *analysis_tools.get_tools(),
            *league_rules_tool.get_tools(),
            *yahoo_login_tool.get_tools(),
            *projection_tool.get_tools(),  # Add projection extraction tools
            remember_fact,  # Add persistent memory tool
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
                
                # Add Playwright MCP server
                # Playwright MCP uses npx to run the server
                if 'playwright' in mcp_config.get('mcpServers', {}):
                    playwright_config = mcp_config['mcpServers']['playwright']
                    
                    try:
                        # Process config env vars
                        playwright_env = {}
                        config_env = playwright_config.get('env', {})
                        for key, value in config_env.items():
                            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                                env_var_name = value[2:-1]
                                env_value = os.environ.get(env_var_name)
                                if env_value is not None:
                                    playwright_env[key] = env_value
                            else:
                                if key not in os.environ:
                                    playwright_env[key] = value
                        
                        # Merge with current environment
                        final_playwright_env = os.environ.copy()
                        final_playwright_env.update(playwright_env)
                        
                        playwright_params = StdioServerParameters(
                            command=playwright_config['command'],
                            args=playwright_config.get('args', []),
                            env=final_playwright_env
                        )
                        
                        # Use StdioConnectionParams for consistency
                        playwright_connection = StdioConnectionParams(
                            server_params=playwright_params,
                            timeout=60.0  # Increased timeout for server startup
                        )
                        
                        playwright_toolset = McpToolset(
                            connection_params=playwright_connection,
                            tool_name_prefix='playwright_'
                        )
                        all_tools.append(playwright_toolset)
                        logger.info("Playwright MCP toolset added successfully")
                    except Exception as e:
                        logger.error(f"Playwright MCP toolset failed to initialize: {e}")
                        logger.error("Playwright MCP will not be available")
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
        
        # Add Research Agent as a tool
        if AGENT_TOOL_AVAILABLE:
            try:
                research_agent = ResearchAgent(model_name=settings.model_name)
                research_tool = AgentTool(agent=research_agent)
                all_tools.append(research_tool)
                logger.info("Added ResearchAgent as a tool")
            except Exception as e:
                logger.error(f"Failed to add ResearchAgent tool: {e}")
        
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
        
        # Register callbacks for state tracking if available
        if ADK_CALLBACKS_AVAILABLE and ADK_IMPORT_STYLE == "new":
            try:
                self.on_before_agent_call = self._track_workflow_state_before
                self.on_after_agent_call = self._track_workflow_state_after
                logger.info("Registered workflow state tracking callbacks")
            except Exception as e:
                logger.warning(f"Could not register callbacks: {e}")
        
        # Register tool error callback to prevent agent stoppage on tool failure
        # Note: We register this regardless of ADK_CALLBACKS_AVAILABLE because LlmAgent supports it
        # even if CallbackContext is not exposed in the top-level module
        try:
            self.on_tool_error_callback = self._handle_tool_error
            logger.info("Registered tool error callback")
        except Exception as e:
            logger.warning(f"Could not register tool error callback: {e}")
        
        # Note: Context optimization is achieved through:
        # 1. Condensed system prompt (see prompts.py) - ~80% reduction
        # 2. The context manager utilities can be used for manual compression if needed
        logger.info("Context-optimized agent initialized (condensed prompts enabled)")
        
    async def _track_workflow_state_before(self, context: Any) -> None:
        """Track workflow state before agent call - initialize task if needed.
        
        Note: This callback modifies context.state directly, which is a "dirty read" pattern
        allowed by ADK Runtime. The state changes will be committed by the Runner after
        the agent yields events. For critical state changes, consider yielding Events with
        state_delta instead, but for callbacks, direct modification is acceptable.
        
        See: https://google.github.io/adk-docs/runtime/#execution-logics-role-agent-tool-callback
        """
        if not ADK_CALLBACKS_AVAILABLE or context is None:
            return
        
        # Initialize task state if this is a new task (use temp: prefix for session-scoped state)
        # Note: Direct state modification is allowed in callbacks (dirty reads pattern)
        # The Runner will commit these changes when processing events
        if 'temp:task_step' not in context.state:
            context.state['temp:task_step'] = 'initializing'
            context.state['task_step'] = 'initializing'  # Also set non-prefixed for compatibility
            context.state['temp:data_gathered'] = []
            context.state['data_gathered'] = []  # Also set non-prefixed
            context.state['has_league_rules'] = False
            context.state['has_roster'] = False
            context.state['has_matchup'] = False
            context.state['temp:task_complete'] = False
            context.state['task_complete'] = False
            logger.debug("Initialized workflow state tracking")
    
    async def _track_workflow_state_after(self, context: Any) -> None:
        """Track workflow state after agent call - detect tool calls and update state.
        
        Also performs automatic fact extraction when the interaction appears to be concluding.
        
        Note: This callback modifies context.state directly, which is a "dirty read" pattern
        allowed by ADK Runtime. The state changes will be committed by the Runner after
        the agent yields events. For critical state changes, consider yielding Events with
        state_delta instead, but for callbacks, direct modification is acceptable.
        
        See: https://google.github.io/adk-docs/runtime/#execution-logics-role-agent-tool-callback
        """
        if not ADK_CALLBACKS_AVAILABLE or context is None:
            return
        
        # Check recent events to detect tool calls
        # Note: We're reading events that were already processed by the Runner
        # This follows the ADK Runtime event loop pattern where the Runner processes
        # events before the agent logic resumes
        if context.events:
            # Look at the last few events to detect tool usage
            for event in reversed(context.events[-5:]):  # Check last 5 events
                # Try to detect tool calls from event content
                # Tool calls typically appear in event content as function calls
                event_str = str(event).lower()
                
                # Detect league rules tools
                if 'get_stored_league_rules' in event_str or 'discover_and_store_league_rules' in event_str:
                    context.state['has_league_rules'] = True
                    if 'league_rules' not in context.state.get('data_gathered', []):
                        data_gathered = context.state.get('data_gathered', [])
                        if isinstance(data_gathered, list):
                            data_gathered.append('league_rules')
                            context.state['data_gathered'] = data_gathered
                
                # Detect roster tools
                if 'yahoo_ff_get_roster' in event_str or 'get_roster' in event_str:
                    context.state['has_roster'] = True
                    if 'roster' not in context.state.get('data_gathered', []):
                        data_gathered = context.state.get('data_gathered', [])
                        if isinstance(data_gathered, list):
                            data_gathered.append('roster')
                            context.state['data_gathered'] = data_gathered
                
                # Detect matchup tools
                if 'yahoo_ff_get_matchup' in event_str or 'get_matchup' in event_str:
                    context.state['has_matchup'] = True
                    if 'matchup' not in context.state.get('data_gathered', []):
                        data_gathered = context.state.get('data_gathered', [])
                        if isinstance(data_gathered, list):
                            data_gathered.append('matchup')
                            context.state['data_gathered'] = data_gathered
                
                # Detect browser actions (executing changes)
                if 'playwright_' in event_str and ('navigate' in event_str or 'click' in event_str or 'fill' in event_str):
                    context.state['temp:has_browser_actions'] = True
            
            # Update task step based on progress (using temp: prefix for session-scoped state)
            current_step = context.state.get('temp:task_step', context.state.get('task_step', 'initializing'))
            
            if current_step == 'initializing' and context.state.get('has_league_rules'):
                context.state['temp:task_step'] = 'gathering_data'
                context.state['task_step'] = 'gathering_data'
            elif current_step == 'gathering_data':
                if context.state.get('has_league_rules') and context.state.get('has_roster'):
                    context.state['temp:task_step'] = 'analyzing'
                    context.state['task_step'] = 'analyzing'
            elif current_step == 'analyzing' and context.state.get('temp:has_browser_actions'):
                context.state['temp:task_step'] = 'executing_actions'
                context.state['task_step'] = 'executing_actions'
            elif current_step == 'executing_actions':
                # Check if we should mark as completing
                if context.state.get('temp:has_browser_actions'):
                    context.state['temp:task_step'] = 'completing'
                    context.state['task_step'] = 'completing'
        
        # Auto-extract facts if this appears to be the final turn of the conversation
        # Detect final turn by checking if the agent has provided a final response without pending actions
        await self._maybe_extract_facts_from_conversation(context)
    
    async def _maybe_extract_facts_from_conversation(self, context: Any) -> None:
        """Extract facts from conversation if it appears to be concluding.
        
        This is called after each agent turn. To avoid extracting facts on every turn,
        we only extract when the conversation appears to be concluding (e.g., when
        the agent provides a final summary or when task is marked complete).
        """
        if not ADK_CALLBACKS_AVAILABLE or context is None:
            return
        
        try:
            # Only extract facts if task appears complete or in 'completing' state
            task_step = context.state.get('temp:task_step', context.state.get('task_step', ''))
            task_complete = context.state.get('temp:task_complete', context.state.get('task_complete', False))
            
            # Check if we've already extracted facts for this session
            facts_extracted = context.state.get('temp:facts_extracted', False)
            
            # Only extract if task is completing/complete AND we haven't extracted yet
            if (task_step == 'completing' or task_complete) and not facts_extracted:
                # Get conversation history
                conversation_history = self._get_conversation_history(context)
                
                # Need at least a few turns to extract meaningful facts
                if len(conversation_history) >= 3:
                    logger.info("Auto-extracting facts from conversation...")
                    
                    # Use LLM to analyze and extract facts
                    extracted_facts = await self._analyze_conversation_for_facts(conversation_history)
                    
                    # Save extracted facts
                    for fact_text in extracted_facts:
                        fact_id = _fact_memory.add_fact(fact_text)
                        logger.info(f"Auto-extracted fact: {fact_text} (ID: {fact_id})")
                    
                    if extracted_facts:
                        logger.info(f"Successfully extracted {len(extracted_facts)} facts from conversation")
                    
                    # Mark facts as extracted for this session
                    context.state['temp:facts_extracted'] = True
        
        except Exception as e:
            logger.error(f"Error during fact extraction: {e}")
            # Don't let fact extraction errors break the agent
    
    def _get_conversation_history(self, context: Any) -> List[Dict[str, str]]:
        """Extract conversation history from context.
        
        Returns:
            List of conversation turns with role and text
        """
        history = []
        
        try:
            # Access conversation history from context events
            if hasattr(context, 'events') and context.events:
                for event in context.events:
                    if hasattr(event, 'content') and event.content:
                        role = 'unknown'
                        if hasattr(event.content, 'role'):
                            role = event.content.role
                        elif hasattr(event, 'author'):
                            role = event.author
                        
                        # Extract text from parts
                        if hasattr(event.content, 'parts') and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    history.append({
                                        'role': role,
                                        'text': part.text
                                    })
        except Exception as e:
            logger.error(f"Error extracting conversation history: {e}")
        
        return history
    
    async def _analyze_conversation_for_facts(self, conversation: List[Dict[str, str]]) -> List[str]:
        """Use LLM to analyze conversation and extract facts worth remembering.
        
        Args:
            conversation: List of conversation turns with role and text
            
        Returns:
            List of fact strings to save
        """
        # Format conversation for analysis
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['text']}"
            for msg in conversation
        ])
        
        # Create analysis prompt
        analysis_prompt = f"""
Analyze the following conversation between a user and a fantasy football agent.
Extract any facts that should be remembered for future interactions.

Focus on:
1. **User Preferences**: Specific likes/dislikes about players, teams, managers, or strategies
2. **Strategic Notes**: Future reminders or planning notes (e.g., "Need backup QB for Week 9")
3. **League Context**: Social dynamics or league-specific culture
4. **Decision Patterns**: Consistent preferences in decision-making (e.g., "Prefers high-floor over boom-bust")

DO NOT extract:
- General football knowledge (can be researched later)
- Temporary information (current week matchups, recent injuries)
- League rules (handled separately by league rules system)
- Transaction details (already recorded in history)

CONVERSATION:
{conversation_text}

Return a JSON array of fact strings to remember. Each fact should be:
- Concise (one sentence)
- Actionable (useful for future decisions)
- Persistent (not time-sensitive)

If no facts should be extracted, return an empty array.

Format: {{"facts": ["fact1", "fact2", ...]}}
"""
        
        try:
            # Use Gemini to analyze
            model = genai.GenerativeModel(settings.model_name)
            response = model.generate_content(analysis_prompt)
            result_text = response.text
            
            # Parse JSON response
            import json
            # Extract JSON from response (may be wrapped in markdown)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            facts = result.get("facts", [])
            
            return facts
        
        except Exception as e:
            logger.error(f"Error analyzing conversation for facts: {e}")
            return []
    
    async def _handle_tool_error(self, tool: Any, args: Dict[str, Any], tool_context: Any, error: Exception) -> Dict[str, Any]:
        """Handle tool execution errors to prevent agent stoppage.
        
        Args:
            tool: The tool that failed
            args: The arguments passed to the tool
            tool_context: The tool context
            error: The exception raised
            
        Returns:
            A dictionary with the error message to be returned to the model
        """
        error_msg = f"Tool '{tool.name}' failed with error: {str(error)}"
        logger.error(error_msg)
        
        # Return a structured error response so the model can see what happened and try again
        return {
            "error": error_msg,
            "status": "failed",
            "suggestion": "Please try again with different arguments or use a different tool."
        }

    @property
    def memory_service(self) -> Optional[BaseMemoryService]:
        """Get the ADK memory service instance."""
        return self._memory_service
    
    def _get_agent_instruction(self) -> str:
        """Get the main instruction for the agent.
        
        Uses the optimized prompt system to reduce token usage while
        maintaining effectiveness. The full prompt is ~80% smaller than
        the original while preserving critical behavior.
        """
        # Include stored league rules in instructions if available
        league_rules_context = ""
        # Safely check if _league_id exists (may not be set during initialization)
        league_id = getattr(self, '_league_id', None)
        if league_id:
            stored_rules = self._league_memory.get_league_rules(league_id)
            if stored_rules:
                league_rules_context = self._league_memory.format_rules_for_agent(league_id)
            else:
                league_rules_context = "⚠️ League rules not yet discovered - discover them first."
        
        # Get stored facts (keep concise)
        facts_context = _fact_memory.get_formatted_facts()
        
        # Build optimized prompt
        prompt = build_agent_prompt(
            league_rules_context=league_rules_context,
            facts_context=facts_context,
            include_workflow_details=True,  # Include on first interaction
            include_browser_tips=False,  # Add dynamically when needed
            include_league_reference=False  # Add dynamically when needed
        )
        
        # Track token usage for debugging
        tokens = estimate_tokens(prompt)
        logger.info(f"System prompt: ~{tokens} tokens (optimized)")
        
        return prompt
    
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
            'message': '⚠️ CRITICAL: Yahoo MCP tools (yahoo_ff_*) are READ-ONLY - they can ONLY fetch data! '
                      'ALL lineup changes MUST be done using Browser MCP tools (browser_*)! '
                      'First ensure league rules are known. If not, discover them from BOTH API and browser. '
                      'Then use yahoo_ff_get_roster and yahoo_ff_get_matchup to get team data (READ-ONLY). '
                      'Use YOUR OWN LLM reasoning to analyze the roster, matchups, and league rules to determine the optimal lineup. '
                      'Then you MUST navigate to Yahoo Fantasy Football website using browser_navigate, '
                      'use browser_snapshot to see the page, and use browser_click to make changes (click to select, click to move).',
            'week': week,
            'note': 'MCP tools are available and will be called by the LLM automatically',
            'required_steps': [
                '1. Check if league rules are known using check_if_rules_known',
                '2. If not known:',
                '   a. Call yahoo_ff_get_league_info for basic settings (READ-ONLY)',
                '   b. Navigate to league settings page via browser_navigate for COMPLETE scoring rules',
                '   c. Store complete rules using discover_and_store_league_rules',
                '3. Get stored league rules using get_stored_league_rules',
                '4. Call yahoo_ff_get_roster to get current team (READ-ONLY)',
                '5. Call yahoo_ff_get_matchup to get weekly matchup (READ-ONLY)',
                '6. Analyze with league rules in mind (PPR vs Standard, position requirements, custom scoring)',
                '7. Use YOUR OWN LLM reasoning to determine optimal lineup based on roster data, matchups, and league rules',
                '8. ⚠️ CRITICAL: Use Browser MCP tools to execute changes:',
                '   - browser_navigate to Yahoo Fantasy Football website',
                '   - browser_snapshot to see page structure',
                '   - browser_click to move players in lineup (click player, then click destination)',
                '   - browser_click to confirm changes',
                '   - browser_screenshot to verify success'
            ],
            'important': 'Yahoo MCP tools are READ-ONLY - Browser MCP tools are REQUIRED for ALL changes!'
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
            'message': '⚠️ CRITICAL: Yahoo MCP tools (yahoo_ff_*) are READ-ONLY - they can ONLY fetch data! '
                      'ALL add/drop actions MUST be done using Browser MCP tools (browser_*)! '
                      'First call yahoo_ff_get_league_info to understand scoring rules (READ-ONLY). '
                      'In PPR leagues, prioritize pass-catching RBs and WRs. '
                      'In Standard leagues, prioritize TD-dependent players. '
                      'Use yahoo_ff_get_waiver_wire or yahoo_ff_get_players to find available players (READ-ONLY). '
                      'Consider your roster needs based on league position requirements. '
                      'Then you MUST navigate to Yahoo Fantasy Football website using browser_navigate, '
                      'use browser_snapshot to see the page, and use browser_click/browser_type to add/drop players.',
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
            'message': '⚠️ CRITICAL: Yahoo MCP tools (yahoo_ff_*) are READ-ONLY - they can ONLY fetch data! '
                      'ALL trade actions MUST be done using Browser MCP tools (browser_*)! '
                      'First call yahoo_ff_get_league_info to understand scoring rules (READ-ONLY). '
                      'Player values differ significantly between PPR and Standard leagues. '
                      'In PPR: Pass-catching RBs and WRs are more valuable. '
                      'In Standard: TD-dependent players are more valuable. '
                      'Use Yahoo Fantasy MCP tools to get trade information and compare teams (READ-ONLY). '
                      'Then you MUST navigate to Yahoo Fantasy Football website using browser_navigate, '
                      'use browser_snapshot to see the page, and use browser_click/browser_type to propose/accept/reject trades.',
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


# Create agent instance (shared across runner + ADK web)
agent = FantasyFootballAgent(memory_service=DEFAULT_MEMORY_SERVICE)
default_memory_service = agent.memory_service

# ADK web UI expects 'root_agent' variable
root_agent = agent

