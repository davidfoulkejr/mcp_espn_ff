from mcp.server.fastmcp import FastMCP
from espn_api.football import League, Team
import json
import os
import sys
import datetime
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("espn-fantasy-football")

# Add stderr logging for Claude Desktop to see
def log_error(message):
    print(message, file=sys.stderr)

def get_credentials():
    try:
        with open('./.venv/secrets.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        log_error("Error: secrets.json file not found. Please create a secrets.json file in the .venv directory with your ESPN_S2 and SWID cookies in order to authenticate automatically.")
        return None
    
def get_owner_name(team) -> str|None:
    return f"{team.owners[0]['firstName']} {team.owners[0]['lastName']}" if team.owners else None

try:
    # Initialize FastMCP server
    log_error("Initializing FastMCP server...")
    mcp = FastMCP("espn-fantasy-football", dependencies=['espn-api'])

    # Constants
    CURRENT_YEAR = datetime.datetime.now().year
    if datetime.datetime.now().month < 7:  # If before July, use previous year
        CURRENT_YEAR -= 1

    log_error(f"Using football year: {CURRENT_YEAR}")
    
    # Store a session map
    SESSION_ID = "default_session"

    class ESPNFantasyFootballAPI:
        def __init__(self):
            self.leagues = {}  # Cache for league objects
            # Store credentials separately per-session rather than globally
            secrets = get_credentials()
            if secrets:
                self.credentials = {
                    SESSION_ID: {
                        'espn_s2': secrets.get('espn_s2'),
                        'swid': secrets.get('swid')
                    }
                }
            else:
                self.credentials = {}

        def get_league(self, session_id, league_id, year=CURRENT_YEAR):
            """Get a league instance with caching, using stored credentials if available"""
            key = f"{league_id}_{year}"
            
            # Check if we have credentials for this session
            espn_s2 = None
            swid = None
            if session_id in self.credentials:
                espn_s2 = self.credentials[session_id].get('espn_s2')
                swid = self.credentials[session_id].get('swid')
            
            # Create league cache key including auth info
            cache_key = f"{key}_{espn_s2}_{swid}"
            
            if cache_key not in self.leagues:
                log_error(f"Creating new league instance for {league_id}, year {year}")
                try:
                    league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)
                    for team in league.teams:
                        team.team_name = team.team_name.strip()
                    self.leagues[cache_key] = league
                except Exception as e:
                    log_error(f"Error creating league: {str(e)}")
                    raise
            
            return self.leagues[cache_key]
        
        def store_credentials(self, session_id, espn_s2, swid):
            """Store credentials for a session"""
            self.credentials[session_id] = {
                'espn_s2': espn_s2,
                'swid': swid
            }
            log_error(f"Stored credentials for session {session_id}")
        
        def clear_credentials(self, session_id):
            """Clear credentials for a session"""
            if session_id in self.credentials:
                del self.credentials[session_id]
                log_error(f"Cleared credentials for session {session_id}")

    # Create our API instance
    api = ESPNFantasyFootballAPI()

    @mcp.tool()
    async def authenticate(espn_s2: str, swid: str) -> str:
        """Store ESPN authentication credentials for this session. Should be done automatically on server start, but can be done manually if needed.
        
        Args:
            espn_s2: The ESPN_S2 cookie value from your ESPN account
            swid: The SWID cookie value from your ESPN account
        """
        try:
            log_error("Authenticating...")
            # Store credentials for this session
            api.store_credentials(SESSION_ID, espn_s2, swid)
            
            return "Authentication successful. Your credentials are stored for this session only."
        except Exception as e:
            log_error(f"Authentication error: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            return f"Authentication error: {str(e)}"

    @mcp.tool()
    async def get_league_info(league_id: int, year: int = CURRENT_YEAR) -> str:
        """Get basic information about a fantasy football league.
        
        Args:
            league_id: The ESPN fantasy football league ID
            year: Optional year for historical data (defaults to current season)
        """
        try:
            log_error(f"Getting league info for league {league_id}, year {year}")
            # Get league using stored credentials
            league = api.get_league(SESSION_ID, league_id, year)
            
            info = {
                "name": league.settings.name,
                "year": league.year,
                "current_week": league.current_week,
                "nfl_week": league.nfl_week,
                "team_count": len(league.teams),
                "teams": [team.team_name for team in league.teams],
                "scoring_type": league.settings.scoring_type,
            }
            
            return str(info)
        except Exception as e:
            log_error(f"Error retrieving league info: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            if "401" in str(e) or "Private" in str(e):
                return ("This appears to be a private league. Please use the authenticate tool first with your "
                      "ESPN_S2 and SWID cookies to access private leagues.")
            return f"Error retrieving league: {str(e)}"

    @mcp.tool()
    async def get_team_roster(league_id: int, team_id: int, year: int = CURRENT_YEAR) -> str:
        """Get a team's current roster.
        
        Args:
            league_id: The ESPN fantasy football league ID
            team_id: The team ID in the league (usually 1-12)
            year: Optional year for historical data (defaults to current season)
        """
        try:
            log_error(f"Getting team roster for league {league_id}, team {team_id}, year {year}")
            # Get league using stored credentials
            league = api.get_league(SESSION_ID, league_id, year)
            
            # Team IDs in ESPN API are 1-based
            if team_id < 1 or team_id > len(league.teams):
                return f"Invalid team_id. Must be between 1 and {len(league.teams)}"
            
            team = league.teams[team_id - 1]
            
            roster_info = {
                "team_name": team.team_name,
                "owner": team.owners,
                "wins": team.wins,
                "losses": team.losses, 
                "roster": []
            }
            
            for player in team.roster:
                [season_stats_key, current_week_key, next_week_key] = player.stats.keys()
                season_stats = player.stats[season_stats_key]
                current_week_stats = player.stats[current_week_key]
                next_week_stats = player.stats[next_week_key]
                roster_info["roster"].append({
                    "name": player.name,
                    "position": player.position,
                    "proTeam": player.proTeam,
                    "injuryStatus": player.injuryStatus,
                    **({"season_total_points": player.total_points} if player.total_points else {}),
                    **({"projected_season_total_points": player.projected_total_points} if player.projected_total_points else {}),
                    "season_stats": season_stats,
                    "current_week_stats": current_week_stats,
                    "next_week_projected_stats": next_week_stats
                })
            
            return str(roster_info)
        except Exception as e:
            log_error(f"Error retrieving team roster: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            if "401" in str(e) or "Private" in str(e):
                return ("This appears to be a private league. Please use the authenticate tool first with your "
                      "ESPN_S2 and SWID cookies to access private leagues.")
            return f"Error retrieving team roster: {str(e)}"
        
    @mcp.tool()
    async def get_team_info(league_id: int, team_id: int = None, team_name: str = "", owner: str = "", year: int = CURRENT_YEAR) -> str:
        """Get a team's general information using its ID, team name, or owner's name. Must include at least one of the three. Return value includes points scored, transactions, etc.
        
        Args:
            league_id: The ESPN fantasy football league ID
            team_id: Optional team ID to search for (1-based index, usually 1-12)
            team_name: Optional team name to search for (case insensitive substring match)
            owner: Optional owner name to search for (case insensitive substring match)
            year: Optional year for historical data (defaults to current season)
        """
        try:
            log_error(f"Getting team roster for league {league_id}, team {team_id}, year {year}")
            # Get league using stored credentials
            league = api.get_league(SESSION_ID, league_id, year)

            team = None
            if team_id:
                # Team IDs in ESPN API are 1-based
                if team_id < 1 or team_id > len(league.teams):
                    return f"Invalid team_id. Must be between 1 and {len(league.teams)}"
                team = league.teams[team_id - 1]
            elif team_name:
                for t in league.teams:
                    if team_name.lower() in t.team_name.lower():
                        team = t
                        break
                if not team:
                    return f"Team with name containing '{team_name}' not found in league {league_id}"
            elif owner:
                for t in league.teams:
                    if any(owner.lower() in f"{o['firstName']} {o['lastName']} {o['displayName']}".lower() for o in t.owners):
                        team = t
                        break
                if not team:
                    return f"Team with owner containing '{owner}' not found in league {league_id}"
            else:
                return "Invalid input. Please provide either team_id, team_name, or owner to identify the team."
            
            team_info = {
                "team_id": team.team_id,
                "team_name": team.team_name,
                "owner": team.owners,
                "wins": team.wins,
                "losses": team.losses,
                "ties": team.ties,
                "points_for": team.points_for,
                "points_against": team.points_against,
                "acquisitions": team.acquisitions,
                "drops": team.drops,
                "trades": team.trades,
                "playoff_pct": team.playoff_pct,
                "final_standing": team.final_standing,
                "outcomes": team.outcomes
            }
            
            return str(team_info)

        except Exception as e:
            log_error(f"Error retrieving team results: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            if "401" in str(e) or "Private" in str(e):
                return ("This appears to be a private league. Please use the authenticate tool first with your "
                      "ESPN_S2 and SWID cookies to access private leagues.")
            return f"Error retrieving team results: {str(e)}"

    @mcp.tool()
    async def get_player_stats(league_id: int, player_name: str, year: int = CURRENT_YEAR) -> str:
        """Get stats for a specific player.
        
        Args:
            league_id: The ESPN fantasy football league ID
            player_name: Name of the player to search for
            year: Optional year for historical data (defaults to current season)
        """
        try:
            log_error(f"Getting player stats for {player_name} in league {league_id}, year {year}")
            # Get league using stored credentials
            league = api.get_league(SESSION_ID, league_id, year)
            
            # Search for player by name
            player = None
            for team in league.teams:
                for roster_player in team.roster:
                    if player_name.lower() in roster_player.name.lower():
                        player = roster_player
                        break
                if player:
                    break
            
            if not player:
                return f"Player '{player_name}' not found in league {league_id}"
            
            # Get player stats
            stats = {
                "name": player.name,
                "position": player.position,
                "team": player.proTeam,
                "points": player.total_points,
                "projected_points": player.projected_total_points,
                "stats": player.stats,
                "injured": player.injured
            }
            
            return str(stats)
        except Exception as e:
            log_error(f"Error retrieving player stats: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            if "401" in str(e) or "Private" in str(e):
                return ("This appears to be a private league. Please use the authenticate tool first with your "
                      "ESPN_S2 and SWID cookies to access private leagues.")
            return f"Error retrieving player stats: {str(e)}"

    @mcp.tool()
    async def get_league_standings(league_id: int, year: int = CURRENT_YEAR) -> str:
        """Get current standings for a league.
        
        Args:
            league_id: The ESPN fantasy football league ID
            year: Optional year for historical data (defaults to current season)
        """
        try:
            log_error(f"Getting league standings for league {league_id}, year {year}")
            # Get league using stored credentials
            league = api.get_league(SESSION_ID, league_id, year)
            
            # Sort teams by wins (descending), then points (descending)
            sorted_teams = sorted(league.teams, 
                                key=lambda x: (x.wins, x.points_for),
                                reverse=True)
            
            standings = []
            for i, team in enumerate(sorted_teams):
                standings.append({
                    "rank": i + 1,
                    "team_name": team.team_name,
                    "owner": team.owners,
                    "wins": team.wins,
                    "losses": team.losses,
                    "points_for": team.points_for,
                    "points_against": team.points_against
                })
            
            return str(standings)
        except Exception as e:
            log_error(f"Error retrieving league standings: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            if "401" in str(e) or "Private" in str(e):
                return ("This appears to be a private league. Please use the authenticate tool first with your "
                      "ESPN_S2 and SWID cookies to access private leagues.")
            return f"Error retrieving league standings: {str(e)}"

    @mcp.tool()
    async def get_weekly_matchups(league_id: int, week: int = None, year: int = CURRENT_YEAR) -> str:
        """Get basic matchup information for all matchups in a specific week, including team names, owners, and scores.
        
        Args:
            league_id: The ESPN fantasy football league ID
            week: The week number (if None, uses previous week)
            year: Optional year for historical data (defaults to current season)
        """
        try:
            # Get league using stored credentials
            league = api.get_league(SESSION_ID, league_id, year)
            
            if week is None:
                prev_week = league.current_week - 1
                log_error(f"No week provided, using previous week (Week {prev_week})")
                week = prev_week

            log_error(f"Getting matchup info for league {league_id}, week {week}, year {year}")
                
            if week < 1 or week > 17:  # Most leagues have 17 weeks max
                return f"Invalid week number. Must be between 1 and 17"
            
            matchups = league.box_scores(week)
            
            matchup_info = []
            for matchup in matchups:
                matchup_info.append({
                    "home_team_id": matchup.home_team.team_id,
                    "home_team": matchup.home_team.team_name,
                    "home_team_owner_name": get_owner_name(matchup.home_team),
                    "home_score": matchup.home_score,
                    "away_team_id": matchup.away_team.team_id if matchup.away_team else None,
                    "away_team": matchup.away_team.team_name if matchup.away_team else "BYE",
                    "away_team_owner_name": get_owner_name(matchup.away_team) if matchup.away_team else None,
                    "away_score": matchup.away_score if matchup.away_team else 0,
                    "winner": "HOME" if matchup.home_score > matchup.away_score else "AWAY" if matchup.away_score > matchup.home_score else "TIE"
                })
            
            return str(matchup_info)
        except Exception as e:
            log_error(f"Error retrieving matchup information: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            if "401" in str(e) or "Private" in str(e):
                return ("This appears to be a private league. Please use the authenticate tool first with your "
                      "ESPN_S2 and SWID cookies to access private leagues.")
            return f"Error retrieving matchup information: {str(e)}"
    
    @mcp.tool()
    async def get_detailed_matchup_info(league_id: int, competitors: list, week: int = None, year: int = CURRENT_YEAR) -> str:
        """Get detailed matchup information for a specific week and list of competitors, including lineup info and player stats.

        Args:
            league_id: The ESPN fantasy football league ID
            competitors: List of team names, owner names, or IDs to filter matchups by (if multiple provided, will include all matchups with at least one of the teams)
            week: The week number (if None, uses current week)
            year: Optional year for historical data (defaults to current season)
        """
        try:
            log_error(f"Getting matchup info for league {league_id}, week {week}, year {year}")
            # Get league using stored credentials
            league = api.get_league(SESSION_ID, league_id, year)
            
            # Default to previous week if not provided (every Tuesday starts a new week, and I almost always use this on Tuesdays)
            if week is None:
                week = league.current_week - 1
                
            if week < 1 or week > 17:  # Most leagues have 17 weeks max
                return f"Invalid week number. Must be between 1 and 17"

            if not competitors:
                return "No competitors provided. Please provide a list of team IDs to filter matchups by."

            # Filter matchups by competitors
            def filter_matchups_by_competitors(matchups, competitors) -> list:
                filtered_matchups = []

                def find_team_matchup(matchup_list, competitor):
                    is_team_id = isinstance(competitor, int)
                    found = None
                    for matchup in matchup_list:
                        if is_team_id:
                            if matchup.home_team.team_id == competitor or (matchup.away_team and matchup.away_team.team_id == competitor):
                                found = matchup
                                break
                        else:
                            search_term = competitor.lower()
                            home = f"{matchup.home_team.team_name} ({get_owner_name(matchup.home_team)})".lower()
                            away = f"{matchup.away_team.team_name} ({get_owner_name(matchup.away_team)})".lower() if matchup.away_team else "BYE"
                            if search_term in home or search_term in away:
                                found = matchup
                                break

                    return found
                
                for c in competitors:
                    matchup = find_team_matchup(matchups, c)
                    if matchup and matchup not in filtered_matchups:
                        filtered_matchups.append(matchup)

                return filtered_matchups

            matchups = filter_matchups_by_competitors(league.box_scores(week), competitors)

            def resolve_lineup(lineup):
                roster = []
                for player in lineup:
                    stats = {}
                    stat_keys = player.stats.keys()
                    # Check if player has stats for this week (if not, they may be on bye)
                    if len(stat_keys) > 0:
                        if week == league.current_week:
                            [season_stats_key, current_week_key, next_week_key] = player.stats.keys()
                            stats = {
                                "season_stats": player.stats[season_stats_key],
                                "weekly_stats": player.stats[current_week_key],
                                "projected_stats": player.stats[next_week_key]
                            }
                        else:
                            [current_week_key] = player.stats.keys()
                            stats = {
                                "weekly_stats": player.stats[current_week_key]
                            }
                    roster.append({
                        "name": player.name,
                        "position": player.position,
                        "proTeam": player.proTeam,
                        "injuryStatus": player.injuryStatus,
                        **({"season_total_points": player.total_points} if player.total_points else {}),
                        **({"projected_season_total_points": player.projected_total_points} if player.projected_total_points else {}),
                        "lineupSlot": player.lineupSlot,
                        **stats
                    })
                return roster

            matchup_info = []
            for matchup in matchups:
                matchup_info.append({
                    "home_team_id": matchup.home_team.team_id,
                    "home_team": matchup.home_team.team_name,
                    "home_team_owner_name": get_owner_name(matchup.home_team),
                    "home_score": matchup.home_score,
                    "home_lineup": resolve_lineup(matchup.home_lineup),
                    "away_team_id": matchup.away_team.team_id if matchup.away_team else None,
                    "away_team": matchup.away_team.team_name if matchup.away_team else "BYE",
                    "away_team_owner_name": get_owner_name(matchup.away_team) if matchup.away_team else None,
                    "away_score": matchup.away_score if matchup.away_team else 0,
                    "away_lineup": resolve_lineup(matchup.away_lineup) if matchup.away_team else [],
                    "winner": "HOME" if matchup.home_score > matchup.away_score else "AWAY" if matchup.away_score > matchup.home_score else "TIE"
                })

            return str(matchup_info)
        except Exception as e:
            log_error(f"Error retrieving matchup information: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            if "401" in str(e) or "Private" in str(e):
                return ("This appears to be a private league. Please use the authenticate tool first with your "
                      "ESPN_S2 and SWID cookies to access private leagues.")
            return f"Error retrieving matchup information: {str(e)}"


    @mcp.tool()
    async def logout() -> str:
        """Clear stored authentication credentials for this session."""
        try:
            log_error("Logging out...")
            # Clear credentials for this session
            api.clear_credentials(SESSION_ID)
            
            return "Authentication credentials have been cleared."
        except Exception as e:
            log_error(f"Error logging out: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            return f"Error logging out: {str(e)}"

    if __name__ == "__main__":
        # Run the server
        log_error("Starting MCP server...")
        mcp.run()
except Exception as e:
    # Log any exception that might occur during server initialization
    log_error(f"ERROR DURING SERVER INITIALIZATION: {str(e)}")
    traceback.print_exc(file=sys.stderr)
    # Keep the process running to see logs
    log_error("Server failed to start, but kept running for logging. Press Ctrl+C to exit.")
    # Wait indefinitely to keep the process alive for logs
    import time
    while True:
        time.sleep(10)