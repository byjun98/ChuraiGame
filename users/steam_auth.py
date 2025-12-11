"""
Steam OpenID Authentication and API Integration
Handles Steam login via OpenID and fetches user library data
"""
import os
import re
import requests
import logging
from urllib.parse import urlencode
from django.conf import settings

logger = logging.getLogger(__name__)

STEAM_API_KEY = os.getenv('STEAM_API_KEY')
STEAM_OPENID_URL = 'https://steamcommunity.com/openid/login'


def get_steam_login_url(return_to_url):
    """
    Generate Steam OpenID login URL
    
    Args:
        return_to_url: URL to redirect back after Steam login
    
    Returns:
        str: Steam OpenID login URL
    """
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'checkid_setup',
        'openid.return_to': return_to_url,
        'openid.realm': return_to_url.split('/users/')[0] + '/',
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
    }
    return f"{STEAM_OPENID_URL}?{urlencode(params)}"


def validate_steam_login(params):
    """
    Validate Steam OpenID response
    
    Args:
        params: Request GET parameters from Steam callback
    
    Returns:
        str or None: Steam ID (64-bit) if valid, None otherwise
    """
    # Check if login was successful
    if params.get('openid.mode') != 'id_res':
        logger.warning("Steam login failed: mode is not id_res")
        return None
    
    # Prepare validation request
    validation_params = {
        'openid.assoc_handle': params.get('openid.assoc_handle', ''),
        'openid.signed': params.get('openid.signed', ''),
        'openid.sig': params.get('openid.sig', ''),
        'openid.ns': params.get('openid.ns', ''),
        'openid.mode': 'check_authentication',
    }
    
    # Add all signed fields
    signed_fields = params.get('openid.signed', '').split(',')
    for field in signed_fields:
        key = f'openid.{field}'
        if key in params:
            validation_params[key] = params[key]
    
    try:
        response = requests.post(STEAM_OPENID_URL, data=validation_params, timeout=10)
        if 'is_valid:true' in response.text:
            # Extract Steam ID from claimed_id
            claimed_id = params.get('openid.claimed_id', '')
            match = re.search(r'https://steamcommunity\.com/openid/id/(\d+)', claimed_id)
            if match:
                steam_id = match.group(1)
                logger.info(f"Steam login validated for Steam ID: {steam_id}")
                return steam_id
    except requests.RequestException as e:
        logger.error(f"Steam validation request failed: {e}")
    
    return None


def get_steam_user_info(steam_id):
    """
    Fetch Steam user profile information
    
    Args:
        steam_id: Steam 64-bit ID
    
    Returns:
        dict or None: User info containing personaname, avatarfull, etc.
    """
    if not STEAM_API_KEY:
        logger.warning("STEAM_API_KEY not configured")
        return None
    
    try:
        url = 'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/'
        params = {
            'key': STEAM_API_KEY,
            'steamids': steam_id
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        players = data.get('response', {}).get('players', [])
        if players:
            player = players[0]
            return {
                'steam_id': steam_id,
                'personaname': player.get('personaname', ''),
                'avatar': player.get('avatar', ''),
                'avatarmedium': player.get('avatarmedium', ''),
                'avatarfull': player.get('avatarfull', ''),
                'profileurl': player.get('profileurl', ''),
                'personastate': player.get('personastate', 0),  # 0=Offline, 1=Online, etc.
            }
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Steam user info for {steam_id}: {e}")
    
    return None


def get_steam_owned_games(steam_id, include_appinfo=True, include_played_free_games=True):
    """
    Fetch user's owned games from Steam API
    
    Args:
        steam_id: Steam 64-bit ID
        include_appinfo: Include game name and image
        include_played_free_games: Include free games with playtime
    
    Returns:
        list: List of game dictionaries with appid, name, playtime_forever, etc.
    """
    if not STEAM_API_KEY:
        logger.warning("STEAM_API_KEY not configured")
        return []
    
    try:
        url = 'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/'
        params = {
            'key': STEAM_API_KEY,
            'steamid': steam_id,
            'include_appinfo': 1 if include_appinfo else 0,
            'include_played_free_games': 1 if include_played_free_games else 0,
            'format': 'json'
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        games = data.get('response', {}).get('games', [])
        logger.info(f"Fetched {len(games)} games for Steam ID {steam_id}")
        
        # Process and return games
        result = []
        for game in games:
            result.append({
                'appid': game.get('appid'),
                'name': game.get('name', ''),
                'playtime_forever': game.get('playtime_forever', 0),  # Minutes
                'playtime_2weeks': game.get('playtime_2weeks', 0),  # Minutes in last 2 weeks
                'img_icon_url': game.get('img_icon_url', ''),
                'img_logo_url': f"https://steamcdn-a.akamaihd.net/steam/apps/{game.get('appid')}/header.jpg",
            })
        
        # Sort by playtime (most played first)
        result.sort(key=lambda x: x['playtime_forever'], reverse=True)
        return result
    
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Steam games for {steam_id}: {e}")
    
    return []


def get_steam_recently_played(steam_id, count=10):
    """
    Fetch user's recently played games
    
    Args:
        steam_id: Steam 64-bit ID
        count: Number of recent games to fetch
    
    Returns:
        list: List of recently played game dictionaries
    """
    if not STEAM_API_KEY:
        logger.warning("STEAM_API_KEY not configured")
        return []
    
    try:
        url = 'https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/'
        params = {
            'key': STEAM_API_KEY,
            'steamid': steam_id,
            'count': count,
            'format': 'json'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        games = data.get('response', {}).get('games', [])
        logger.info(f"Fetched {len(games)} recently played games for Steam ID {steam_id}")
        
        result = []
        for game in games:
            result.append({
                'appid': game.get('appid'),
                'name': game.get('name', ''),
                'playtime_forever': game.get('playtime_forever', 0),
                'playtime_2weeks': game.get('playtime_2weeks', 0),
                'img_icon_url': game.get('img_icon_url', ''),
                'img_logo_url': f"https://steamcdn-a.akamaihd.net/steam/apps/{game.get('appid')}/header.jpg",
            })
        
        return result
    
    except requests.RequestException as e:
        logger.error(f"Failed to fetch recently played games for {steam_id}: {e}")
    
    return []


def get_game_recommendations_from_library(steam_id, limit=20):
    """
    Generate game recommendations based on user's Steam library
    
    Args:
        steam_id: Steam 64-bit ID
        limit: Number of recommendations to return
    
    Returns:
        dict: Contains 'most_played', 'genres', and 'recommendations'
    """
    owned_games = get_steam_owned_games(steam_id)
    recently_played = get_steam_recently_played(steam_id)
    
    if not owned_games:
        return {
            'most_played': [],
            'total_games': 0,
            'total_playtime_hours': 0,
            'recently_played': recently_played,
        }
    
    # Calculate total playtime
    total_playtime = sum(g['playtime_forever'] for g in owned_games)
    total_hours = round(total_playtime / 60, 1)
    
    # Get top 10 most played games
    most_played = owned_games[:10]
    
    return {
        'most_played': most_played,
        'total_games': len(owned_games),
        'total_playtime_hours': total_hours,
        'recently_played': recently_played,
        'library': owned_games[:50],  # Return top 50 by playtime
    }
