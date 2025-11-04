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
    [matchup] = await call_mcp_tool("get_detailed_matchup_info", {"league_id": league_id, "year": 2025, "competitors": ['Erin']})
    print(f"{matchup['home_team_owner_name']}'s lineup:")
    for player in matchup['home_lineup']:
        injury = player['injuryStatus'] if 'injuryStatus' in player else 'healthy'
        print(f'{player['lineupSlot']} {player['name']}: {player['weekly_stats']['points'] if 'points' in player['weekly_stats'] else 0} ({injury})')

    print(f"{matchup['away_team_owner_name']}'s lineup:")
    for player in matchup['away_lineup']:
        injury = player['injuryStatus'] if 'injuryStatus' in player else 'healthy'
        print(f'{player['lineupSlot']} {player['name']}: {player['weekly_stats']['points'] if 'points' in player['weekly_stats'] else 0} ({injury})')
    # matchups = await call_mcp_tool("get_weekly_matchups", {"league_id": league_id})
    # for m in matchups:
    #     print(f"{m['home_team_owner_name'].split(' ')[0]} vs. {m['away_team_owner_name'].split(' ')[0] if m['away_team_owner_name'] else 'BYE'}")
    
    # maxPoints = 0
    # for i in range(1,10):
    #     matchups = await call_mcp_tool('get_weekly_matchups', {"league_id": league_id, "week": i})
    #     for m in matchups:
    #         if m['home_score'] > maxPoints:
    #             maxPoints = m['home_score']
    #         if m['away_score'] > maxPoints:
    #             maxPoints = m['away_score']

    # print(f"Highest total of the year: {maxPoints}")

if __name__ == "__main__":
    asyncio.run(main())