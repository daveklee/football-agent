"""Tool to extract player projections from Yahoo Fantasy website."""
import logging
from typing import List, Dict, Any
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)


class ProjectionExtractorTool:
    """Tool to help extract projections from Yahoo Fantasy website."""
    
    def get_tools(self) -> List[FunctionTool]:
        """Get projection extraction tools."""
        return [
            FunctionTool(func=self.get_projection_extraction_script),
            FunctionTool(func=self.parse_projection_data),
        ]
    
    async def get_projection_extraction_script(self) -> Dict[str, Any]:
        """Get a JavaScript snippet to extract player projections from Yahoo Fantasy My Team page.
        
        This returns JavaScript code that should be run via playwright__browser_evaluate
        after navigating to your Yahoo Fantasy team page.
        
        Returns:
            Dict with the JavaScript code and instructions
        """
        script = '''
(function() {
    const players = [];
    
    // Find all player rows in the roster table
    const rows = document.querySelectorAll('table tbody tr, [class*="player"], [data-player]');
    
    // Also try the specific Yahoo Fantasy roster structure
    const rosterRows = document.querySelectorAll('.Ptable-body .Ta-start, .ysf-player-row, tr[class*="player"]');
    
    // Method 1: Parse visible table with Proj Pts column
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        const headers = Array.from(table.querySelectorAll('th, thead td')).map(h => h.textContent.trim().toLowerCase());
        const projIndex = headers.findIndex(h => h.includes('proj'));
        const nameIndex = headers.findIndex(h => h.includes('player') || h.includes('offense') || h === 'name');
        const posIndex = headers.findIndex(h => h.includes('pos'));
        
        if (projIndex > -1) {
            const bodyRows = table.querySelectorAll('tbody tr');
            bodyRows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length > projIndex) {
                    const projText = cells[projIndex]?.textContent?.trim();
                    const projection = parseFloat(projText);
                    
                    // Try to get player name from various locations
                    let playerName = '';
                    const nameLink = row.querySelector('a[href*="players"]');
                    if (nameLink) {
                        playerName = nameLink.textContent.trim();
                    } else if (nameIndex > -1 && cells[nameIndex]) {
                        playerName = cells[nameIndex].textContent.trim().split('\\n')[0];
                    }
                    
                    // Get position
                    let position = '';
                    const posCell = row.querySelector('[class*="pos"], .Pos');
                    if (posCell) {
                        position = posCell.textContent.trim();
                    } else if (posIndex > -1 && cells[posIndex]) {
                        position = cells[posIndex].textContent.trim();
                    }
                    
                    if (playerName && !isNaN(projection)) {
                        players.push({
                            name: playerName,
                            position: position,
                            projected_points: projection,
                            source: 'yahoo_website'
                        });
                    }
                }
            });
        }
    });
    
    // Method 2: Try direct text parsing for Yahoo's specific structure
    if (players.length === 0) {
        document.querySelectorAll('tr').forEach(row => {
            const text = row.textContent;
            // Look for patterns like "Player Name ... 24.63"
            const nameEl = row.querySelector('a[href*="players"], .ysf-player-name');
            if (nameEl) {
                const name = nameEl.textContent.trim();
                // Find projection in the row (usually a number between 0-50)
                const projMatch = text.match(/(\\d{1,2}\\.\\d{2})(?!%)/);
                if (projMatch) {
                    const proj = parseFloat(projMatch[1]);
                    if (proj > 0 && proj < 60) {  // Reasonable projection range
                        players.push({
                            name: name,
                            projected_points: proj,
                            source: 'yahoo_website_parsed'
                        });
                    }
                }
            }
        });
    }
    
    return {
        success: true,
        player_count: players.length,
        players: players,
        page_url: window.location.href,
        timestamp: new Date().toISOString()
    };
})();
'''
        
        return {
            "script": script,
            "instructions": """
To extract projections from Yahoo Fantasy:

1. First, get your league info using yahoo__ff_get_leagues to find the league URL

2. Navigate to your team page using playwright__browser_navigate
   (URL format: https://football.fantasysports.yahoo.com/f1/LEAGUE_ID)

3. Wait for the page to load:
   playwright__browser_wait_for with time: 2

4. Run this extraction script:
   playwright__browser_evaluate with expression: [use the script field from this response]

5. The script returns player names and their projected points (Proj Pts column)

6. Use these projections for lineup decisions - they are league-specific!
""",
            "note": "These projections use YOUR league's scoring rules and are the most accurate for YOUR league."
        }
    
    async def parse_projection_data(
        self,
        raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse and organize projection data extracted from the website.
        
        Args:
            raw_data: The data returned from the extraction script
            
        Returns:
            Organized projection data for lineup decisions
        """
        if not raw_data or not raw_data.get("success"):
            return {
                "error": "No projection data provided",
                "suggestion": "Run get_projection_extraction_script first and pass the result"
            }
        
        players = raw_data.get("players", [])
        
        if not players:
            return {
                "error": "No players found in data",
                "suggestion": "Make sure you're on the My Team page and the roster is visible"
            }
        
        # Sort by projected points
        sorted_players = sorted(players, key=lambda p: p.get("projected_points", 0), reverse=True)
        
        # Group by position if available
        by_position = {}
        for player in sorted_players:
            pos = player.get("position", "UNKNOWN")
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(player)
        
        return {
            "success": True,
            "total_players": len(players),
            "players_sorted_by_projection": sorted_players,
            "players_by_position": by_position,
            "top_projected": sorted_players[:5] if len(sorted_players) >= 5 else sorted_players,
            "recommendation": "Start players with highest projected points, considering position requirements"
        }

