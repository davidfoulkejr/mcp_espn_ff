# ESPN Fantasy Football MCP Server

This is a Model Context Protocol (MCP) server that connects Claude to ESPN Fantasy Football data. It was previously run locally, but is now **hosted on Azure and auto-deploys on every push to main**.

### Note on this fork

This fork has been adapted from the original repo and tailored to fit my specific needs. Specifically, I added a new tool `get_detailed_matchup_info` which returns detailed info for a single matchup so that I can ask my AI agent, "Give me a summary of the week 6 matchup between team ID 3 and team ID 7" and it will have access to those teams' lineups and each player's stats for that week. I also added a way to search for a specific team by its ID, team name, or owner name so that I can say, "Tell me John Doe's record so far this season" or "How did Blue Team do last week?"

## Overview

This MCP server allows LLMs like Claude to interact with the ESPN Fantasy Football API through an HTTP-based remote connection. It runs as a stateless service on Azure App Service and can be added to Claude as a custom connector.

## Deployment

### Current Setup

- **Hosting**: Azure App Service (Linux, Python 3.12)
- **Transport**: HTTP (streamable-http)
- **Auto-deploy**: GitHub Actions with OIDC authentication
- **URL**: `https://df26-espn-fantasy-football-api.azurewebsites.net`

### Local Development

For local testing, you can still run the server locally via:

```bash
pip install -r requirements.txt
python espn_fantasy_server.py
```

The server will start on `http://localhost:8000` with HTTP transport instead of stdio.

## Configuration

### Environment Variables

The server reads ESPN authentication credentials and the API token from environment variables:

- **`ESPN_S2`** - Your ESPN `espn_s2` cookie (for private leagues)
- **`ESPN_SWID`** - Your ESPN `SWID` cookie (for private leagues)
- **`MCP_AUTH_TOKEN`** - Bearer token for authenticating requests (set this as a secret in Claude)
- **`PORT`** - Port to run the server on (default: 8000)
- **`WEBSITES_PORT`** - Azure-specific port configuration (automatically set to 8000)

**Local development fallback**: If `ESPN_S2` and `ESPN_SWID` are not set, the server will try to load credentials from `.venv/secrets.json` for backwards compatibility.

### Getting ESPN Credentials

1. Log in to ESPN Fantasy Football
2. Open your browser's Developer Tools (F12)
3. Go to **Network** tab
4. Refresh the page
5. Click on any ESPN API request
6. Look for cookies: `espn_s2` and `SWID`
7. Copy these values

**Never commit these to git** — always use environment variables.

## Features (MCP Tools)

- **Authentication**: Securely store ESPN credentials for the current session (for private leagues)
- **League Info**: Get basic information about fantasy football leagues
- **Team Rosters**: View current team rosters and player details
- **Player Stats**: Find and display stats for specific players
- **League Standings**: View current team rankings and performance metrics
- **Matchup Information**: Get details about weekly matchups

## Adding to Claude Desktop

### Setup

1. Get your auth token (provided during deployment — save it somewhere secure)
2. In Claude Desktop, go to **Settings** → **Developers** → **Manage Custom Connectors**
3. Click **Add Custom Connector**
4. Enter:
   - **Name**: `ESPN Fantasy Football`
   - **MCP Server URL**: `https://df26-espn-fantasy-football-api.azurewebsites.net`
   - **Authentication Type**: Bearer Token
   - **Token**: Your `MCP_AUTH_TOKEN` (the 40-character token from deployment)
5. Click **Save**
6. Restart Claude Desktop

### Usage

Once connected, you can ask Claude:
- "Get me the standings for my league (league ID: 12345)"
- "Show me team 3's roster"
- "Who's winning the matchup between team 2 and team 5 this week?"
- "Tell me John Doe's record"

## Features (MCP Tools)

- **Authentication**: Securely store ESPN credentials for the current session (for private leagues)
- **League Info**: Get basic information about fantasy football leagues
- **Team Rosters**: View current team rosters and player details
- **Player Stats**: Find and display stats for specific players
- **League Standings**: View current team rankings and performance metrics
- **Matchup Information**: Get details about weekly matchups


## Acknowledgements

[cwendt94/espn-api](https://github.com/cwendt94/espn-api) for the nifty python wrapper around the ESPN Fantasy API


<!-- Azure deployment fix: corrected federated credential issuer -->

<!-- Fixed: Added subscription-level RBAC role assignment -->
