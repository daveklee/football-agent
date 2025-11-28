
import sys
import os
sys.path.append(os.getcwd())
from app.utils.database_league_memory import DatabaseLeagueRulesMemory

def check_db():
    try:
        memory = DatabaseLeagueRulesMemory()
        leagues = memory.get_all_leagues()
        print(f"Found {len(leagues)} leagues in database.")
        for league_id, rules in leagues.items():
            print(f"League ID: {league_id}")
            print(f"  Name: {rules.get('league_name')}")
            print(f"  Scoring: {rules.get('scoring_type')}")
            print(f"  Updated: {rules.get('updated_at')}")
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_db()
