# Yahoo Fantasy Football MCP Server

This project uses the excellent [Yahoo Fantasy Football MCP Server](https://github.com/derekrbreese/fantasy-football-mcp-public) by [@derekrbreese](https://github.com/derekrbreese).

## Features

The MCP server provides comprehensive Yahoo Fantasy Football functionality:

### League & Team Management
- `ff_get_leagues` - List all leagues for your authenticated Yahoo account
- `ff_get_league_info` - Retrieve detailed league metadata and team information
- `ff_get_standings` - View current league standings with wins, losses, and points
- `ff_get_roster` - Inspect detailed roster information for any team
- `ff_get_matchup` - Analyze weekly matchup details and projections
- `ff_compare_teams` - Side-by-side team roster comparisons for trades/analysis

### Advanced Lineup Optimization
- `ff_build_lineup` - Generate optimal lineups using advanced optimization algorithms
  - Smart FLEX decisions accounting for different position baselines
  - Multi-source projections (Yahoo and Sleeper expert rankings)
  - Strategy-based optimization (Conservative, Aggressive, Balanced)
  - Volatility scoring (Floor vs ceiling analysis)
  - Position-normalized FLEX calculations

### Player Discovery & Waiver Wire
- `ff_get_players` - Browse available free agents with ownership percentages
- `ff_get_waiver_wire` - Smart waiver wire targets with expert analysis
- `ff_get_draft_rankings` - Access Yahoo's pre-draft rankings and ADP data

### Draft Assistant Tools
- `ff_get_draft_recommendation` - AI-powered draft pick suggestions
- `ff_analyze_draft_state` - Real-time roster needs and positional analysis
- `ff_get_draft_results` - Post-draft analysis with grades and team summaries

### Advanced Analytics
- `ff_analyze_reddit_sentiment` - Social media sentiment analysis for player buzz
- `ff_get_api_status` - Monitor cache performance and Yahoo API rate limiting
- `ff_clear_cache` - Clear cached responses for fresh data
- `ff_refresh_token` - Automatically refresh Yahoo OAuth tokens

### Player Enhancement Layer

The server includes an enhancement layer that enriches player data with:
- **Bye Week Detection** - Automatically zeros projections for players on bye
- **Recent Performance Stats** - Last 1-3 weeks of actual performance from Sleeper API
- **Performance Flags** - Intelligent alerts:
  - `BREAKOUT_CANDIDATE` - Recent performance > 150% of projection
  - `TRENDING_UP` - Recent performance exceeds projection
  - `DECLINING_ROLE` - Recent performance < 70% of projection
  - `HIGH_CEILING` - Explosive upside potential
  - `CONSISTENT` - Reliable, steady performance
- **Adjusted Projections** - Blends recent reality with stale projections

## Installation

The server is automatically cloned during setup via `setup.sh`. If you need to set it up manually:

```bash
git clone https://github.com/derekrbreese/fantasy-football-mcp-public.git
cd fantasy-football-mcp-public
pip install -r requirements.txt
```

## Configuration

The server requires Yahoo OAuth tokens. Set these up using the included scripts:

```bash
cd fantasy-football-mcp-public
python setup_yahoo_auth.py
```

Or for re-authentication:

```bash
python reauth_yahoo.py
```

This will generate:
- `YAHOO_ACCESS_TOKEN`
- `YAHOO_REFRESH_TOKEN`
- `YAHOO_GUID`

Add these to your `.env` file.

## Usage in This Project

The MCP server is configured in `mcp_config.json` and will be automatically used by the ADK agent. The agent's `YahooFantasyTools` class provides a compatibility layer, but the actual data access goes through the MCP server.

## Documentation

For complete documentation, see the [fantasy-football-mcp-public repository](https://github.com/derekrbreese/fantasy-football-mcp-public).

## Credits

This MCP server is developed and maintained by [@derekrbreese](https://github.com/derekrbreese). All credit for the Yahoo Fantasy Football integration goes to that project.

