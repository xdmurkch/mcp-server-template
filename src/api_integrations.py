#!/usr/bin/env python3
"""
Multi-platform API integration for checking friend status across Discord, Steam, and Riot Games.
"""
import os
import aiohttp
from typing import Dict, List, Optional, Any
from enum import Enum


class Platform(str, Enum):
    """Supported platforms"""
    DISCORD = "discord"
    STEAM = "steam"
    RIOT = "riot"


class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, platform: str, message: str, status_code: Optional[int] = None):
        self.platform = platform
        self.message = message
        self.status_code = status_code
        super().__init__(f"[{platform}] {message}")


class DiscordAPI:
    """Discord API integration for presence checking"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("DISCORD_TOKEN")
        self.base_url = "https://discord.com/api/v10"

    async def get_user_presence(self, user_id: str) -> Dict[str, Any]:
        """
        Get Discord user presence status

        Args:
            user_id: Discord user ID

        Returns:
            Dict with user presence information

        Raises:
            APIError: If API call fails
        """
        if not self.token:
            raise APIError("discord", "DISCORD_TOKEN environment variable not set")

        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Get user information
                async with session.get(
                    f"{self.base_url}/users/{user_id}",
                    headers=headers
                ) as response:
                    if response.status == 401:
                        raise APIError("discord", "Invalid Discord token", 401)
                    elif response.status == 404:
                        raise APIError("discord", f"User {user_id} not found", 404)
                    elif response.status != 200:
                        text = await response.text()
                        raise APIError("discord", f"API error: {text}", response.status)

                    user_data = await response.json()

                    return {
                        "user_id": user_id,
                        "username": user_data.get("username"),
                        "discriminator": user_data.get("discriminator"),
                        "status": "online",  # Note: Bot API has limited presence access
                        "platform": "discord"
                    }

        except aiohttp.ClientError as e:
            raise APIError("discord", f"Network error: {str(e)}")
        except Exception as e:
            raise APIError("discord", f"Unexpected error: {str(e)}")

    async def get_online_friends(self) -> List[Dict[str, Any]]:
        """
        Get list of online Discord friends
        Note: Requires user token and proper OAuth scopes

        Returns:
            List of online friend objects

        Raises:
            APIError: If API call fails
        """
        if not self.token:
            raise APIError("discord", "DISCORD_TOKEN environment variable not set")

        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Note: Bot accounts cannot access friends list
                # This would require a user token with proper OAuth scopes
                raise APIError("discord", "Friends list requires user token with OAuth scopes")

        except aiohttp.ClientError as e:
            raise APIError("discord", f"Network error: {str(e)}")


class SteamAPI:
    """Steam API integration for friend status checking"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("STEAM_API_KEY")
        self.base_url = "https://api.steampowered.com"

    async def get_friend_status(self, steam_id: str) -> Dict[str, Any]:
        """
        Get Steam user's online status

        Args:
            steam_id: Steam 64-bit ID

        Returns:
            Dict with user status information

        Raises:
            APIError: If API call fails
        """
        if not self.api_key:
            raise APIError("steam", "STEAM_API_KEY environment variable not set")

        try:
            async with aiohttp.ClientSession() as session:
                # Get player summaries
                async with session.get(
                    f"{self.base_url}/ISteamUser/GetPlayerSummaries/v0002/",
                    params={
                        "key": self.api_key,
                        "steamids": steam_id
                    }
                ) as response:
                    if response.status == 403:
                        raise APIError("steam", "Invalid Steam API key", 403)
                    elif response.status != 200:
                        text = await response.text()
                        raise APIError("steam", f"API error: {text}", response.status)

                    data = await response.json()
                    players = data.get("response", {}).get("players", [])

                    if not players:
                        raise APIError("steam", f"Steam ID {steam_id} not found", 404)

                    player = players[0]

                    # Map personastate to human-readable status
                    status_map = {
                        0: "offline",
                        1: "online",
                        2: "busy",
                        3: "away",
                        4: "snooze",
                        5: "looking_to_trade",
                        6: "looking_to_play"
                    }

                    persona_state = player.get("personastate", 0)

                    return {
                        "user_id": steam_id,
                        "username": player.get("personaname"),
                        "status": status_map.get(persona_state, "unknown"),
                        "game": player.get("gameextrainfo"),
                        "platform": "steam"
                    }

        except aiohttp.ClientError as e:
            raise APIError("steam", f"Network error: {str(e)}")
        except Exception as e:
            raise APIError("steam", f"Unexpected error: {str(e)}")

    async def get_online_friends(self, steam_id: str) -> List[Dict[str, Any]]:
        """
        Get list of online Steam friends for a user

        Args:
            steam_id: Steam 64-bit ID of the user

        Returns:
            List of online friend objects

        Raises:
            APIError: If API call fails
        """
        if not self.api_key:
            raise APIError("steam", "STEAM_API_KEY environment variable not set")

        try:
            async with aiohttp.ClientSession() as session:
                # Get friends list
                async with session.get(
                    f"{self.base_url}/ISteamUser/GetFriendList/v0001/",
                    params={
                        "key": self.api_key,
                        "steamid": steam_id,
                        "relationship": "friend"
                    }
                ) as response:
                    if response.status == 401:
                        raise APIError("steam", "Friends list is private or invalid Steam ID", 401)
                    elif response.status != 200:
                        text = await response.text()
                        raise APIError("steam", f"API error: {text}", response.status)

                    data = await response.json()
                    friends = data.get("friendslist", {}).get("friends", [])

                    if not friends:
                        return []

                    # Get status for all friends
                    friend_ids = [friend["steamid"] for friend in friends]

                    # Steam API allows up to 100 IDs at once
                    online_friends = []
                    for i in range(0, len(friend_ids), 100):
                        batch = friend_ids[i:i+100]
                        async with session.get(
                            f"{self.base_url}/ISteamUser/GetPlayerSummaries/v0002/",
                            params={
                                "key": self.api_key,
                                "steamids": ",".join(batch)
                            }
                        ) as batch_response:
                            if batch_response.status == 200:
                                batch_data = await batch_response.json()
                                players = batch_data.get("response", {}).get("players", [])

                                # Filter online players (personastate > 0)
                                for player in players:
                                    if player.get("personastate", 0) > 0:
                                        online_friends.append({
                                            "user_id": player["steamid"],
                                            "username": player.get("personaname"),
                                            "status": "online",
                                            "game": player.get("gameextrainfo"),
                                            "platform": "steam"
                                        })

                    return online_friends

        except aiohttp.ClientError as e:
            raise APIError("steam", f"Network error: {str(e)}")
        except Exception as e:
            raise APIError("steam", f"Unexpected error: {str(e)}")


class RiotAPI:
    """Riot Games API integration for summoner and presence checking"""

    def __init__(self, api_key: Optional[str] = None, region: str = "na1"):
        self.api_key = api_key or os.environ.get("RIOT_API_KEY")
        self.region = region
        self.base_url = f"https://{region}.api.riotgames.com"

    async def get_summoner_by_name(self, summoner_name: str) -> Dict[str, Any]:
        """
        Get summoner information by name

        Args:
            summoner_name: League of Legends summoner name

        Returns:
            Dict with summoner information

        Raises:
            APIError: If API call fails
        """
        if not self.api_key:
            raise APIError("riot", "RIOT_API_KEY environment variable not set")

        headers = {
            "X-Riot-Token": self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Get summoner by name (using RIOT ID format: name#tag)
                async with session.get(
                    f"{self.base_url}/lol/summoner/v4/summoners/by-name/{summoner_name}",
                    headers=headers
                ) as response:
                    if response.status == 403:
                        raise APIError("riot", "Invalid Riot API key or rate limited", 403)
                    elif response.status == 404:
                        raise APIError("riot", f"Summoner {summoner_name} not found", 404)
                    elif response.status != 200:
                        text = await response.text()
                        raise APIError("riot", f"API error: {text}", response.status)

                    data = await response.json()

                    return {
                        "user_id": data.get("id"),
                        "summoner_name": data.get("name"),
                        "summoner_level": data.get("summonerLevel"),
                        "puuid": data.get("puuid"),
                        "platform": "riot"
                    }

        except aiohttp.ClientError as e:
            raise APIError("riot", f"Network error: {str(e)}")
        except Exception as e:
            raise APIError("riot", f"Unexpected error: {str(e)}")

    async def get_active_game(self, summoner_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active game information for a summoner

        Args:
            summoner_id: Encrypted summoner ID

        Returns:
            Dict with active game info, or None if not in game

        Raises:
            APIError: If API call fails
        """
        if not self.api_key:
            raise APIError("riot", "RIOT_API_KEY environment variable not set")

        headers = {
            "X-Riot-Token": self.api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/lol/spectator/v4/active-games/by-summoner/{summoner_id}",
                    headers=headers
                ) as response:
                    if response.status == 404:
                        # Not in game
                        return None
                    elif response.status == 403:
                        raise APIError("riot", "Invalid Riot API key or rate limited", 403)
                    elif response.status != 200:
                        text = await response.text()
                        raise APIError("riot", f"API error: {text}", response.status)

                    data = await response.json()

                    return {
                        "game_mode": data.get("gameMode"),
                        "game_type": data.get("gameType"),
                        "game_length": data.get("gameLength"),
                        "status": "in_game",
                        "platform": "riot"
                    }

        except aiohttp.ClientError as e:
            raise APIError("riot", f"Network error: {str(e)}")
        except Exception as e:
            raise APIError("riot", f"Unexpected error: {str(e)}")


class MultiPlatformAPI:
    """Unified interface for all platform APIs"""

    def __init__(self):
        self.discord = DiscordAPI()
        self.steam = SteamAPI()
        self.riot = RiotAPI()

    async def get_friend_status(self, platform: str, user_id: str) -> Dict[str, Any]:
        """
        Get friend status across any platform

        Args:
            platform: Platform name (discord, steam, riot)
            user_id: User identifier for the platform

        Returns:
            Dict with user status information

        Raises:
            APIError: If API call fails or platform is unsupported
        """
        platform = platform.lower()

        try:
            if platform == Platform.DISCORD:
                return await self.discord.get_user_presence(user_id)
            elif platform == Platform.STEAM:
                return await self.steam.get_friend_status(user_id)
            elif platform == Platform.RIOT:
                summoner = await self.riot.get_summoner_by_name(user_id)
                active_game = await self.riot.get_active_game(summoner["user_id"])

                return {
                    **summoner,
                    "status": "in_game" if active_game else "offline",
                    "game_info": active_game
                }
            else:
                raise APIError(
                    "multi_platform",
                    f"Unsupported platform: {platform}. Supported platforms: discord, steam, riot"
                )
        except APIError:
            raise
        except Exception as e:
            raise APIError(platform, f"Unexpected error: {str(e)}")

    async def get_online_friends(self, platforms: Optional[List[str]] = None, steam_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get online friends across all platforms

        Args:
            platforms: List of platforms to check (default: all)
            steam_id: Required for Steam friends list

        Returns:
            Dict with online friends grouped by platform

        Raises:
            APIError: If API calls fail
        """
        if platforms is None:
            platforms = [Platform.DISCORD, Platform.STEAM, Platform.RIOT]

        results = {
            "online_friends": {},
            "errors": {}
        }

        for platform in platforms:
            platform = platform.lower()
            try:
                if platform == Platform.DISCORD:
                    friends = await self.discord.get_online_friends()
                    results["online_friends"]["discord"] = friends
                elif platform == Platform.STEAM:
                    if not steam_id:
                        results["errors"]["steam"] = "steam_id parameter required for Steam friends"
                        continue
                    friends = await self.steam.get_online_friends(steam_id)
                    results["online_friends"]["steam"] = friends
                elif platform == Platform.RIOT:
                    # Riot API doesn't have a friends list endpoint
                    results["errors"]["riot"] = "Riot API does not support friends list"
            except APIError as e:
                results["errors"][platform] = str(e)

        return results
