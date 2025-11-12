#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastmcp import FastMCP

# Handle both direct execution and module import
try:
    from api_integrations import MultiPlatformAPI, APIError
except ImportError:
    from src.api_integrations import MultiPlatformAPI, APIError

mcp = FastMCP("Multi-Platform Friend Status MCP Server")
api = MultiPlatformAPI()

@mcp.tool(description="Greet a user by name with a welcome message from the MCP server")
def greet(name: str) -> str:
    return f"Hello, {name}! Welcome to our sample MCP server running on Heroku!"

@mcp.tool(description="Get information about the MCP server including name, version, environment, and Python version")
def get_server_info() -> dict:
    return {
        "server_name": "Multi-Platform Friend Status MCP Server",
        "version": "2.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0],
        "supported_platforms": ["discord", "steam", "riot"]
    }

@mcp.tool(description="Get friend status across Discord, Steam, or Riot platforms. Returns online status, username, and game info if available.")
async def get_friend_status(platform: str, user_id: str) -> dict:
    """
    Check the online status of a friend on a specific platform

    Args:
        platform: The platform to check (discord, steam, riot)
        user_id: The user identifier (Discord user ID, Steam 64-bit ID, or Riot summoner name)

    Returns:
        Dict containing user status information

    Example:
        get_friend_status("steam", "76561198000000000")
        get_friend_status("discord", "123456789012345678")
        get_friend_status("riot", "SummonerName")
    """
    try:
        result = await api.get_friend_status(platform, user_id)
        return {
            "success": True,
            "data": result
        }
    except APIError as e:
        return {
            "success": False,
            "error": {
                "platform": e.platform,
                "message": e.message,
                "status_code": e.status_code
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "platform": platform,
                "message": f"Unexpected error: {str(e)}"
            }
        }

@mcp.tool(description="Get list of online friends across multiple platforms (Discord, Steam, Riot). Returns aggregated results with error handling.")
async def get_online_friends(platforms: str = "discord,steam,riot", steam_id: str = None) -> dict:
    """
    Get online friends across multiple platforms

    Args:
        platforms: Comma-separated list of platforms to check (default: "discord,steam,riot")
        steam_id: Required for Steam - your Steam 64-bit ID to retrieve friends list

    Returns:
        Dict containing online friends grouped by platform and any errors encountered

    Example:
        get_online_friends()
        get_online_friends(platforms="steam", steam_id="76561198000000000")
        get_online_friends(platforms="discord,steam", steam_id="76561198000000000")
    """
    try:
        platform_list = [p.strip() for p in platforms.split(",")]
        result = await api.get_online_friends(platforms=platform_list, steam_id=steam_id)
        return {
            "success": True,
            "data": result
        }
    except APIError as e:
        return {
            "success": False,
            "error": {
                "platform": e.platform,
                "message": e.message,
                "status_code": e.status_code
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "message": f"Unexpected error: {str(e)}"
            }
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting FastMCP server on {host}:{port}")
    
    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )
