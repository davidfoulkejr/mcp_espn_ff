import asyncio
import json
import ast
import pprint
import sys
import time
from espn_fantasy_server import mcp, get_credentials, get_owner_name
from mcp.types import TextContent

SESSION_ID = 'default_session'

async def call_mcp_tool(tool_name, params):
    response = await mcp.call_tool(tool_name, params)
    if isinstance(response[0], TextContent):
        return ast.literal_eval(response[0].text)
    raise Exception(f"Unexpected response type: {type(response)}")

async def main():
    secrets = get_credentials()
    if not secrets:
        print("No credentials found")
        sys.exit(1)
    league_id = secrets['league_id']
    # [matchup] = await call_mcp_tool("get_detailed_matchup_info", {"league_id": league_id, "year": 2025, "competitors": ["David", "Stephen"]})
    # print(f"{matchup['home_team_owner_name']}'s lineup:")
    # for player in matchup['home_lineup']:
    #     print(f'{player['lineupSlot']} {player['name']}: {player['weekly_stats']['points'] if 'points' in player['weekly_stats'] else 0}')

    # print(f"{matchup['away_team_owner_name']}'s lineup:")
    # for player in matchup['away_lineup']:
    #     print(f'{player['lineupSlot']} {player['name']}: {player['weekly_stats']['points'] if 'points' in player['weekly_stats'] else 0}')
    standings = await call_mcp_tool("get_league_standings", {"league_id": league_id})
    for team in standings:
        print(f"{team['owner'][0]['firstName']}: {team['wins']}-{team['losses']}")

if __name__ == "__main__":
    asyncio.run(main())