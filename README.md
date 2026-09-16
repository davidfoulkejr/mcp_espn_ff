# ESPN Fantasy Football MCP Server

A remote Model Context Protocol server that exposes ESPN Fantasy Football data
to clients such as Claude. It runs on Azure App Service using FastMCP's native
streamable HTTP transport and deploys from `main` through GitHub Actions.

## Hosted service

- **Runtime:** Azure App Service on Linux with Python 3.12
- **MCP endpoint:** `https://df26-espn-fantasy-football-api.azurewebsites.net/mcp/<MCP_ROUTE_TOKEN>`
- **Health endpoint:** `https://df26-espn-fantasy-football-api.azurewebsites.net/`
- **Authentication:** Secret capability URL
- **Deployment:** GitHub Actions using Azure OIDC

The base URL is only a health endpoint. MCP clients must use the complete secret
MCP URL. Treat that URL like a password and rotate it if it is exposed.

## Environment variables

- `MCP_ROUTE_TOKEN` - Required random token embedded in the MCP URL path
- `ESPN_S2` - ESPN `espn_s2` cookie for private leagues
- `ESPN_SWID` - ESPN `SWID` cookie for private leagues
- `PORT` - Listening port; defaults to 8000
- `WEBSITES_PORT` - Azure App Service port, configured as 8000

Credentials are read only from environment variables. Never commit them to Git.

## Local development

Create a standard Python virtual environment and install `requirements.txt`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:MCP_ROUTE_TOKEN = "replace-with-a-long-random-route-token"
$env:ESPN_S2 = "your-espn-s2-cookie"
$env:ESPN_SWID = "{your-espn-swid}"

python espn_fantasy_server.py
```

The local MCP endpoint is
`http://localhost:8000/mcp/<MCP_ROUTE_TOKEN>`.

## Add the connector to Claude

1. Open **Settings** -> **Connectors** -> **Add custom connector**.
2. Enter `ESPN Fantasy Football` as the name.
3. Enter
   `https://df26-espn-fantasy-football-api.azurewebsites.net/mcp/<MCP_ROUTE_TOKEN>`
   as the MCP server URL.
4. Leave the optional OAuth client ID and client secret fields blank.
5. Save the connector. Claude will treat it as an authless server; possession
   of the complete URL is what grants access.

## MCP tools

- `get_weekly_matchups`
- `get_detailed_matchup_info`
- `get_league_standings`
- `get_team_roster`
- `get_team_info`

Additional tools support league information, player statistics, and runtime
ESPN authentication management.

## Getting ESPN credentials

1. Sign in to ESPN Fantasy Football.
2. Open the browser developer tools and select the **Network** tab.
3. Refresh the page and inspect an ESPN API request.
4. Copy the `espn_s2` and `SWID` cookie values into the corresponding
   environment variables.

## Acknowledgements

[cwendt94/espn-api](https://github.com/cwendt94/espn-api) provides the Python
wrapper used to access the ESPN Fantasy API.
