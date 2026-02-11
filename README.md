# Multi-Platform Friend Status MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server for checking friend status across Discord, Steam, and Riot Games platforms. Deployed via Render with streamable HTTP transport.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/InteractionCo/mcp-server-template)

## Features

This MCP server provides tools to check friend status across multiple gaming platforms:

- **Discord**: Check user presence and status
- **Steam**: Get friend online status and current game
- **Riot Games**: Summoner lookup and active game detection

### Available Tools

1. `get_friend_status(platform, user_id)` - Check status of a specific friend
2. `get_online_friends(platforms, steam_id)` - Get all online friends across platforms

## API Setup

Before deploying, you'll need API credentials for each platform:

### Discord API
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the bot token
5. Set `DISCORD_TOKEN` environment variable

### Steam API
1. Visit [Steam API Key Registration](https://steamcommunity.com/dev/apikey)
2. Register for an API key (requires Steam account)
3. Copy your API key
4. Set `STEAM_API_KEY` environment variable

### Riot Games API
1. Go to [Riot Developer Portal](https://developer.riotgames.com/)
2. Sign in with your Riot account
3. Register your application
4. Copy your API key
5. Set `RIOT_API_KEY` environment variable

### Setting Environment Variables in Render

1. Go to your Render dashboard
2. Select your web service
3. Navigate to "Environment" tab
4. Add the following environment variables:
   - `DISCORD_TOKEN` - Your Discord bot token
   - `STEAM_API_KEY` - Your Steam Web API key
   - `RIOT_API_KEY` - Your Riot Games API key

See `.env.example` for a complete list of required environment variables.

## Local Development

### Setup

Fork the repo, then run:

```bash
git clone <your-repo-url>
cd mcp-server-template
conda create -n mcp-server python=3.13
conda activate mcp-server
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Test

```bash
python src/server.py
# then in another terminal run:
npx @modelcontextprotocol/inspector
```

Open http://localhost:3000 and connect to `http://localhost:8000/mcp` using "Streamable HTTP" transport (NOTE THE `/mcp`!).

## Deployment

### Option 1: One-Click Deploy
Click the "Deploy to Render" button above.

### Option 2: Manual Deployment
1. Fork this repository
2. Connect your GitHub account to Render
3. Create a new Web Service on Render
4. Connect your forked repository
5. Render will automatically detect the `render.yaml` configuration

Your server will be available at `https://your-service-name.onrender.com/mcp` (NOTE THE `/mcp`!)

## Poke Setup

You can connect your MCP server to Poke at (poke.com/settings/connections)[poke.com/settings/connections].
To test the connection explitly, ask poke somethink like `Tell the subagent to use the "{connection name}" integration's "{tool name}" tool`.
If you run into persistent issues of poke not calling the right MCP (e.g. after you've renamed the connection) you may send `clearhistory` to poke to delete all message history and start fresh.
We're working hard on improving the integration use of Poke :)


## Usage Examples

### Check Steam Friend Status
```python
# Via Poke:
"Check if my friend with Steam ID 76561198000000000 is online"

# Returns:
{
  "success": true,
  "data": {
    "user_id": "76561198000000000",
    "username": "PlayerName",
    "status": "online",
    "game": "Counter-Strike 2",
    "platform": "steam"
  }
}
```

### Get All Online Friends
```python
# Via Poke:
"Get all my online friends on Steam"
# Provide your Steam ID: 76561198000000000

# Returns:
{
  "success": true,
  "data": {
    "online_friends": {
      "steam": [
        {
          "user_id": "76561198000000001",
          "username": "Friend1",
          "status": "online",
          "game": "Dota 2",
          "platform": "steam"
        }
      ]
    },
    "errors": {}
  }
}
```

### Check Riot Summoner Status
```python
# Via Poke:
"Check if Faker is in a game on Riot"

# Returns:
{
  "success": true,
  "data": {
    "user_id": "...",
    "summoner_name": "Faker",
    "status": "in_game",
    "game_info": {
      "game_mode": "CLASSIC",
      "game_type": "MATCHED_GAME"
    }
  }
}
```

## Error Handling

All tools include comprehensive error handling:

- **Invalid API Keys**: Returns clear error message indicating which key is invalid
- **Rate Limiting**: Catches 403 errors and indicates rate limiting
- **User Not Found**: Returns 404 status with helpful message
- **Network Errors**: Catches connection issues and timeouts
- **Missing Parameters**: Validates required parameters

Example error response:
```json
{
  "success": false,
  "error": {
    "platform": "steam",
    "message": "STEAM_API_KEY environment variable not set",
    "status_code": null
  }
}
```

## Customization

Add more tools by decorating functions with `@mcp.tool`:

```python
@mcp.tool(description="Your tool description")
async def your_custom_tool(param: str) -> dict:
    """Your tool implementation."""
    try:
        # Your logic here
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```
