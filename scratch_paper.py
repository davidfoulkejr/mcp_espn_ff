import asyncio
import json
import ast
import pprint
import sys
import time
from espn_fantasy_server import mcp, get_credentials
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
    matchups = await call_mcp_tool("get_weekly_matchups", {"league_id": league_id, "week": 7, "year": 2025})
    print(json.dumps(matchups))

if __name__ == "__main__":
    asyncio.run(main())