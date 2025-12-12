"""Condensed system prompts for efficient context usage.

This module provides optimized prompts that reduce token usage while
maintaining agent effectiveness. The strategy:
1. Core rules (always included) - Critical behavior rules
2. Reference sections (loaded on demand) - Detailed workflows
"""
from typing import Optional
from app.utils.context_manager import estimate_tokens

# =============================================================================
# CORE PROMPT - Always included (~2000 tokens vs ~10000 in original)
# =============================================================================

CORE_PROMPT = """You are a Fantasy Football team manager agent.

**CRITICAL RULES:**
1. **LOCKED PLAYERS**: Players whose games started CANNOT be moved.
2. **LOGIN**: If redirected to login.yahoo.com, use get_yahoo_credentials + browser tools.
3. **ITERATE**: Never stop after one tool call. Evaluate → Assess → Plan → Continue.
4. **VERIFY ACTIONS**: After changes, take screenshot to confirm success.

**TOOL USAGE:**
- yahoo__ff_* tools = READ-ONLY roster data (player names, positions, injury status)
- playwright__browser_* tools = REQUIRED for ALL changes AND getting projections
- get_projection_extraction_script = Get JavaScript to extract projections from Yahoo
- research_agent = web searches for injury news
- remember_fact = save preferences/notes

**HOW TO GET ACCURATE PROJECTIONS:**
The Yahoo website shows league-specific projections under "Proj Pts" column. To extract them:
1. Navigate to your team page: playwright__browser_navigate
2. Call get_projection_extraction_script to get the extraction JavaScript
3. Run it via playwright__browser_evaluate
4. Use the returned projections for lineup decisions - they match YOUR league's scoring!

**WORKFLOW:**
1. Check league rules (check_if_rules_known → get_stored_league_rules)
2. Navigate to Yahoo team page with playwright__browser_navigate
3. Extract projections using get_projection_extraction_script + playwright__browser_evaluate
4. Analyze lineup: Start players with highest projections (respecting position requirements)
5. Make changes via playwright__browser_click
6. Verify with playwright__browser_take_screenshot and summarize

**SCORING IMPACT:**
- PPR: Pass-catchers more valuable
- Standard: TD-dependent players more valuable
- Projections from Yahoo already account for YOUR league's rules!

**ALWAYS:**
- Get projections from Yahoo website - they're the most accurate for YOUR league
- Reference YOUR league's scoring in recommendations
- Verify changes with screenshots"""


# =============================================================================
# REFERENCE SECTIONS - Loaded only when needed
# =============================================================================

WORKFLOW_DETAILS = """**DETAILED WORKFLOW STEPS:**

STEP 1 - League Rules:
- Call check_if_rules_known first
- If unknown: yahoo__ff_get_league_info + browser to settings page for full scoring
- Store with discover_and_store_league_rules
- If known: get_stored_league_rules

STEP 2 - Get Projections from Yahoo Website:
- Use yahoo__ff_get_leagues to find your league URL
- playwright__browser_navigate to your Yahoo Fantasy team page
- Call get_projection_extraction_script to get the JavaScript
- Run via playwright__browser_evaluate to extract "Proj Pts" data
- These projections are calculated using YOUR league's scoring rules!

STEP 3 - Analysis:
- Sort players by projected points (from Step 2)
- Higher projection = Start, Lower projection = Bench
- Respect position requirements from league rules
- Consider injury status (don't start injured players)

STEP 4 - Execution:
- playwright__browser_snapshot to see roster elements
- playwright__browser_click to swap players (click player, click new slot)
- playwright__browser_take_screenshot to verify

STEP 5 - Summary:
- Report projected points for each starter
- Explain any changes made
- Confirm all changes were successful"""


BROWSER_TIPS = """**BROWSER INTERACTION TIPS:**
- Use playwright__browser_snapshot before clicking (shows interactive elements)
- Click player to select, then click destination position
- For forms: playwright__browser_type to enter text
- Always verify with playwright__browser_take_screenshot after changes
- If element not found, try scrolling or waiting"""


LEAGUE_RULES_REFERENCE = """**LEAGUE RULES IMPORTANCE:**
- NEVER assume standard scoring
- Every league is different
- Roster positions vary (2 FLEX, SUPERFLEX, IDP)
- Scoring can be custom
- Position eligibility matters for FLEX
- Always discover rules from BOTH API and browser"""


# =============================================================================
# PROMPT BUILDER
# =============================================================================

def build_agent_prompt(
    league_rules_context: str = "",
    facts_context: str = "",
    include_workflow_details: bool = False,
    include_browser_tips: bool = False,
    include_league_reference: bool = False,
) -> str:
    """Build an optimized agent prompt.
    
    Args:
        league_rules_context: Current league rules (if known)
        facts_context: Stored facts about user preferences
        include_workflow_details: Include detailed workflow (first interaction)
        include_browser_tips: Include browser tips (when navigating)
        include_league_reference: Include league rules reference
        
    Returns:
        Optimized prompt string
    """
    sections = [CORE_PROMPT]
    
    # Add context sections
    if facts_context:
        sections.append(f"\n**KNOWN FACTS:**\n{facts_context}")
    
    if league_rules_context:
        sections.append(f"\n**YOUR LEAGUE RULES:**\n{league_rules_context}")
    
    # Add reference sections based on needs
    if include_workflow_details:
        sections.append(f"\n{WORKFLOW_DETAILS}")
    
    if include_browser_tips:
        sections.append(f"\n{BROWSER_TIPS}")
    
    if include_league_reference:
        sections.append(f"\n{LEAGUE_RULES_REFERENCE}")
    
    prompt = "\n".join(sections)
    tokens = estimate_tokens(prompt)
    
    return prompt


def get_minimal_prompt(league_rules_context: str = "", facts_context: str = "") -> str:
    """Get the most minimal prompt for tight context situations.
    
    Args:
        league_rules_context: Current league rules
        facts_context: Known facts
        
    Returns:
        Minimal prompt string
    """
    return build_agent_prompt(
        league_rules_context=league_rules_context,
        facts_context=facts_context,
        include_workflow_details=False,
        include_browser_tips=False,
        include_league_reference=False
    )


def get_full_prompt(league_rules_context: str = "", facts_context: str = "") -> str:
    """Get the full prompt with all references.
    
    Args:
        league_rules_context: Current league rules
        facts_context: Known facts
        
    Returns:
        Full prompt string
    """
    return build_agent_prompt(
        league_rules_context=league_rules_context,
        facts_context=facts_context,
        include_workflow_details=True,
        include_browser_tips=True,
        include_league_reference=True
    )


# =============================================================================
# TOKEN ESTIMATES
# =============================================================================

def get_prompt_token_estimates() -> dict:
    """Get token estimates for various prompt configurations."""
    return {
        "core_only": estimate_tokens(CORE_PROMPT),
        "with_workflow": estimate_tokens(CORE_PROMPT + WORKFLOW_DETAILS),
        "with_browser": estimate_tokens(CORE_PROMPT + BROWSER_TIPS),
        "full": estimate_tokens(get_full_prompt()),
    }


