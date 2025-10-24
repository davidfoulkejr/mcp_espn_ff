# ESPN Fantasy Football MCP Server

### Note on this fork

This fork has been adapted from the original repo and tailored to fit my specific needs. Specifically, I added a new tool `get_detailed_matchup_info` which returns detailed info for a single matchup so that I can ask my AI agent, "Give me a summary of the week 6 matchup between team ID 3 and team ID 7" and it will have access to those teams' lineups and each player's stats for that week. I also added a way to search for a specific team by its ID, team name, or owner name so that I can say, "Tell me John Doe's record so far this season" or "How did Blue Team do last week?"

I also added a check to pull the authentication information automatically from a file called `.venv/secrets.json` (which is git-ignored) so I don't have to copy/paste the auth info every single time I restart the server.

## Overview

This MCP (Model Context Protocol) server allows LLMs like Claude to interact with the ESPN Fantasy Football API. It provides tools for accessing league data, team rosters, player statistics, and more through a standardized interface. It can work with both public and private ESPN Leagues.

## Features (MCP Tools)

- **Authentication**: Securely store ESPN credentials for the current session (for private leagues)
- **League Info**: Get basic information about fantasy football leagues
- **Team Rosters**: View current team rosters and player details
- **Player Stats**: Find and display stats for specific players
- **League Standings**: View current team rankings and performance metrics
- **Matchup Information**: Get details about weekly matchups

## Installation

### Prerequisites

- Python 3.10 or higher
- `uv` package manager
- [Claude Desktop](https://claude.ai/download) for the best experience

### Usage with Claude Desktop

1. Update the Claude Desktop config:
- MacOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Include reference to the MCP server
  ```json
  {
  "mcpServers": {
    "espn-fantasy-football": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/directory",
        "run",
        "espn_fantasy_server.py"
        ]
      }
    } 
  }
2. Restart Claude Desktop


## Acknowledgements

[cwendt94/espn-api](https://github.com/cwendt94/espn-api) for the nifty python wrapper around the ESPN Fantasy API

