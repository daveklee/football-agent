"""League-level MCP tool handlers (leagues, standings, teams)."""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.api import yahoo_api_call


# These functions need to be imported from main file since they use global cache
# We'll import them when updating fantasy_football_multi_league.py
async def discover_leagues():
    """Placeholder - will be imported from main module."""
    raise NotImplementedError("Must import from fantasy_football_multi_league")


async def get_user_team_info(league_key):
    """Placeholder - will be imported from main module."""
    raise NotImplementedError("Must import from fantasy_football_multi_league")


async def get_all_teams_info(league_key):
    """Placeholder - will be imported from main module."""
    raise NotImplementedError("Must import from fantasy_football_multi_league")


async def handle_ff_get_leagues(arguments: Dict) -> Dict:
    """Get all fantasy football leagues for the authenticated user.

    Args:
        arguments: Empty dict (no arguments required)

    Returns:
        Dict with total_leagues and list of league summaries
    """
    leagues = await discover_leagues()

    if not leagues:
        return {
            "error": "No active NFL leagues found",
            "suggestion": "Make sure your Yahoo token is valid and you have active leagues",
        }

    return {
        "total_leagues": len(leagues),
        "leagues": [
            {
                "key": league["key"],
                "name": league["name"],
                "teams": league["num_teams"],
                "current_week": league["current_week"],
                "scoring": league["scoring_type"],
            }
            for league in leagues.values()
        ],
    }


def _extract_roster_positions(settings_data: Dict) -> List[Dict[str, Any]]:
    """Parse Yahoo league settings response to extract roster positions."""
    roster_positions: list[Dict[str, Any]] = []

    def _add_position(pos_info: Dict[str, Any]) -> None:
        if not isinstance(pos_info, dict):
            return
        position = pos_info.get("position")
        count = pos_info.get("count", 1)
        if position:
            roster_positions.append(
                {
                    "position": position,
                    "count": count,
                    "position_type": pos_info.get("position_type"),
                }
            )

    try:
        content = settings_data.get("fantasy_content", {}).get("league", {})
        # Yahoo sometimes returns list structure
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "settings" in item:
                    league_settings = item["settings"]
                    if isinstance(league_settings, list):
                        for setting in league_settings:
                            if isinstance(setting, dict) and "roster_positions" in setting:
                                roster_data = setting["roster_positions"]
                                if isinstance(roster_data, list):
                                    for pos in roster_data:
                                        if isinstance(pos, dict) and "roster_position" in pos:
                                            _add_position(pos["roster_position"])
                                elif isinstance(roster_data, dict):
                                    for key, value in roster_data.items():
                                        if key != "count" and isinstance(value, dict):
                                            if "roster_position" in value:
                                                _add_position(value["roster_position"])
        elif isinstance(content, dict) and "settings" in content:
            roster_data = content["settings"].get("roster_positions", [])
            for pos in roster_data:
                _add_position(pos)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Error parsing roster positions: {exc}")

    return roster_positions


def _extract_scoring_settings(settings_data: Dict) -> Dict[str, Any]:
    """Extract key scoring modifiers (e.g., PPR settings) and common scoring rules."""
    scoring_details: Dict[str, Any] = {"stat_modifiers": {}}
    scoring_format = "Unknown"
    ppr_value: Optional[float] = None

    # Note: Yahoo uses numeric stat IDs. Stat ID "9" is known to be receptions (PPR).
    # Other stat IDs vary by league configuration and may include custom scoring.
    
    try:
        content = settings_data.get("fantasy_content", {}).get("league", {})
        stats_container: Optional[list] = None

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "stat_modifiers" in item:
                    modifiers = item["stat_modifiers"]
                    if isinstance(modifiers, dict):
                        stats_container = modifiers.get("stats")
        elif isinstance(content, dict) and "stat_modifiers" in content:
            stats_container = content["stat_modifiers"].get("stats")

        if isinstance(stats_container, list):
            for stat_entry in stats_container:
                if not isinstance(stat_entry, dict):
                    continue
                stat_id = str(stat_entry.get("stat_id"))
                value = stat_entry.get("value")
                scoring_details["stat_modifiers"][stat_id] = value
                
                # Extract key scoring values for easier reference
                if stat_id == "9":  # receptions (PPR)
                    try:
                        ppr_value = float(value)
                    except (TypeError, ValueError):
                        ppr_value = None
                elif stat_id == "0":  # passing yards
                    try:
                        scoring_details["pass_yds_per_point"] = float(value)
                    except (TypeError, ValueError):
                        pass
                elif stat_id == "3":  # rushing yards
                    try:
                        scoring_details["rush_yds_per_point"] = float(value)
                    except (TypeError, ValueError):
                        pass
                elif stat_id == "5":  # receiving yards
                    try:
                        scoring_details["rec_yds_per_point"] = float(value)
                    except (TypeError, ValueError):
                        pass
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Error parsing scoring settings: {exc}")

    if ppr_value is not None:
        if abs(ppr_value - 1.0) < 1e-6:
            scoring_format = "PPR"
        elif abs(ppr_value - 0.5) < 1e-6:
            scoring_format = "Half-PPR"
        elif ppr_value == 0:
            scoring_format = "Standard"
        scoring_details["ppr_points_per_reception"] = ppr_value

    scoring_details["scoring_format"] = scoring_format
    
    # Add implications for agent understanding
    if scoring_format == "PPR":
        scoring_details["implications"] = "Pass-catching RBs and WRs are SIGNIFICANTLY more valuable. Prioritize players with high reception counts."
    elif scoring_format == "Half-PPR":
        scoring_details["implications"] = "Pass-catchers get moderate boost. Balance between PPR and Standard strategies."
    elif scoring_format == "Standard":
        scoring_details["implications"] = "TD-dependent players are more valuable. Prioritize goal-line RBs and red-zone targets."
    
    return scoring_details


def _derive_position_eligibility(roster_positions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Provide eligibility info for FLEX/SUPERFLEX positions and detect non-standard formats."""
    eligibility: Dict[str, list[str]] = {}
    flex_mapping = {
        "FLEX": ["RB", "WR", "TE"],
        "W/R/T": ["WR", "RB", "TE"],
        "W/R": ["WR", "RB"],
        "W/T": ["WR", "TE"],
        "R/T": ["RB", "TE"],
        "SUPERFLEX": ["QB", "RB", "WR", "TE"],
        "Q/W/R/T": ["QB", "WR", "RB", "TE"],
        "OP": ["QB", "RB", "WR", "TE"],
        "UTIL": ["RB", "WR", "TE"],
    }
    
    # Track QB counts to detect 2QB leagues
    qb_count = 0
    superflex_count = 0

    for pos in roster_positions:
        name = pos.get("position", "").upper()
        count = pos.get("count", 1)
        
        if not name:
            continue
            
        # Count QBs and SUPERFLEX positions
        if name == "QB":
            qb_count += count
        elif name in ["SUPERFLEX", "OP", "Q/W/R/T"]:
            superflex_count += count
            
        # Map flex positions
        if name in flex_mapping:
            eligibility[pos.get("position")] = flex_mapping[name]
        # Handle case-insensitive matching
        elif name in [k.upper() for k in flex_mapping.keys()]:
            for key in flex_mapping.keys():
                if key.upper() == name:
                    eligibility[pos.get("position")] = flex_mapping[key]
                    break

    # Add metadata about league type
    if qb_count >= 2 or superflex_count > 0:
        eligibility["_league_type"] = "SUPERFLEX/2QB" if qb_count >= 2 or superflex_count > 0 else "Standard"
        eligibility["_qb_value_multiplier"] = 1.5 if (qb_count >= 2 or superflex_count > 0) else 1.0

    return eligibility


async def handle_ff_get_league_info(arguments: Dict) -> Dict:
    """Get detailed information about a specific league.

    Args:
        arguments: Dict with 'league_key'

    Returns:
        Dict with league details and your team summary
    """
    if not arguments.get("league_key"):
        return {"error": "league_key is required"}

    league_key = arguments.get("league_key")

    leagues = await discover_leagues()
    if league_key not in leagues:
        return {
            "error": f"League {league_key} not found",
            "available_leagues": list(leagues.keys()),
        }

    league = leagues[league_key]
    team_info = await get_user_team_info(league_key)
    settings_data = await yahoo_api_call(f"league/{league_key}/settings")
    roster_positions = _extract_roster_positions(settings_data)
    scoring_settings = _extract_scoring_settings(settings_data)
    position_eligibility = _derive_position_eligibility(roster_positions)

    return {
        "league": league["name"],
        "key": league_key,
        "season": league["season"],
        "teams": league["num_teams"],
        "current_week": league["current_week"],
        "scoring_type": league["scoring_type"],
        "status": "active" if not league["is_finished"] else "finished",
        "roster_positions": roster_positions,
        "scoring_settings": scoring_settings,
        "position_eligibility": position_eligibility,
        "your_team": {
            "name": team_info.get("team_name", "Unknown") if team_info else "Not found",
            "key": team_info.get("team_key") if team_info else None,
            "draft_position": team_info.get("draft_position") if team_info else None,
            "draft_grade": team_info.get("draft_grade") if team_info else None,
        },
    }


async def handle_ff_get_standings(arguments: Dict) -> Dict:
    """Get current standings for a league.

    Args:
        arguments: Dict with 'league_key'

    Returns:
        Dict with league_key and sorted standings list
    """
    if not arguments.get("league_key"):
        return {"error": "league_key is required"}

    league_key = arguments.get("league_key")
    data = await yahoo_api_call(f"league/{league_key}/standings")

    standings = []
    league = data.get("fantasy_content", {}).get("league", [])

    for item in league:
        if isinstance(item, dict) and "standings" in item:
            standings_list = item["standings"]
            teams = {}
            if isinstance(standings_list, list) and standings_list:
                teams = standings_list[0].get("teams", {})
            elif isinstance(standings_list, dict):
                teams = standings_list.get("teams", {})

            for key, team_entry in teams.items():
                if key == "count" or not isinstance(team_entry, dict):
                    continue
                if "team" in team_entry:
                    team_array = team_entry["team"]
                    team_info = {}
                    team_standings = {}
                    if isinstance(team_array, list) and team_array:
                        core = team_array[0]
                        if isinstance(core, list):
                            for elem in core:
                                if isinstance(elem, dict) and "name" in elem:
                                    team_info["name"] = elem["name"]
                        for part in team_array[1:]:
                            if isinstance(part, dict) and "team_standings" in part:
                                team_standings = part["team_standings"]

                    if team_info and team_standings:
                        standings.append(
                            {
                                "rank": team_standings.get("rank", 0),
                                "team": team_info.get("name", "Unknown"),
                                "wins": team_standings.get("outcome_totals", {}).get("wins", 0),
                                "losses": team_standings.get("outcome_totals", {}).get("losses", 0),
                                "ties": team_standings.get("outcome_totals", {}).get("ties", 0),
                                "points_for": team_standings.get("points_for", 0),
                                "points_against": team_standings.get("points_against", 0),
                            }
                        )

    standings.sort(key=lambda row: row["rank"])
    return {"league_key": league_key, "standings": standings}


async def handle_ff_get_teams(arguments: Dict) -> Dict:
    """Get all teams in a league.

    Args:
        arguments: Dict with 'league_key'

    Returns:
        Dict with league_key, teams list, and total_teams count
    """
    if not arguments.get("league_key"):
        return {"error": "league_key is required"}

    league_key: Optional[str] = arguments.get("league_key")
    if league_key is None:
        return {"error": "league_key cannot be None"}

    teams_info = await get_all_teams_info(league_key)
    return {
        "league_key": league_key,
        "teams": teams_info,
        "total_teams": len(teams_info),
    }
