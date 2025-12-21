import os
import requests
import logging
from django.conf import settings
from .models import Game, GameScreenshot, GameTrailer, Tag

# Configure logging
logger = logging.getLogger(__name__)

RAWG_API_KEY = os.getenv('RAWG_API_KEY')
BASE_URL = "https://api.rawg.io/api"

# 태그 유형 매핑 (RAWG 태그 분류용)
GENRE_TAGS = {
    'action', 'shooter', 'fps', 'platformer', 'fighting', 'beat-em-up',
    'rpg', 'jrpg', 'action-rpg', 'mmorpg', 'roguelike', 'roguelite',
    'adventure', 'puzzle', 'strategy', 'rts', 'turn-based-strategy', 'tactical',
    'simulation', 'racing', 'sports', 'card', 'board-game', 'visual-novel',
    'survival', 'horror', 'survival-horror', 'stealth', 'sandbox',
    'metroidvania', 'souls-like', 'hack-and-slash', 'dungeon-crawler',
    'tower-defense', 'city-builder', 'management', 'life-sim', 'dating-sim'
}

THEME_TAGS = {
    'sci-fi', 'cyberpunk', 'fantasy', 'dark-fantasy', 'medieval', 'post-apocalyptic',
    'horror', 'comedy', 'mystery', 'thriller', 'historical', 'military', 'war',
    'space', 'underwater', 'western', 'steampunk', 'noir', 'anime', 'cartoon',
    'lovecraftian', 'zombies', 'vampires', 'robots', 'dinosaurs', 'dragons',
    'mythology', 'pirates', 'ninjas', 'samurai', 'aliens', 'demons'
}

FEATURE_TAGS = {
    'singleplayer', 'multiplayer', 'co-op', 'online-co-op', 'local-co-op',
    'pvp', 'online-pvp', 'local-multiplayer', 'split-screen', 'mmo',
    'open-world', 'linear', 'non-linear', 'procedural-generation',
    'controller-support', 'vr', 'moddable', 'level-editor',
    'cross-platform', 'free-to-play', 'early-access', 'indie', 'aaa',
    'story-rich', 'exploration', 'crafting', 'building', 'base-building',
    'character-customization', 'choices-matter', 'multiple-endings',
    'first-person', 'third-person', 'top-down', 'isometric', 'side-scroller',
    '2d', '3d', 'pixel-graphics', 'retro', 'realistic'
}

MOOD_TAGS = {
    'relaxing', 'casual', 'difficult', 'hardcore', 'challenging',
    'atmospheric', 'funny', 'cute', 'dark', 'emotional', 'violent',
    'gore', 'mature', 'family-friendly', 'beautiful', 'colorful'
}

def get_tag_type(slug):
    """태그 slug로 태그 유형 결정"""
    slug_lower = slug.lower()
    if slug_lower in GENRE_TAGS:
        return 'genre'
    elif slug_lower in THEME_TAGS:
        return 'theme'
    elif slug_lower in FEATURE_TAGS:
        return 'feature'
    elif slug_lower in MOOD_TAGS:
        return 'mood'
    else:
        return 'feature'  # 기본값

def get_rawg_game_id(game_title, steam_appid=None):
    """
    Search for a game by title and optionally Steam AppID, return its RAWG ID.
    Tries to find the best match using Steam store link if available.
    """
    if not RAWG_API_KEY:
        logger.warning("RAWG_API_KEY not found in environment variables.")
        return None

    # Strategy 1: Search by Steam AppID (most accurate)
    if steam_appid:
        try:
            params = {
                'key': RAWG_API_KEY,
                'stores': '1',  # 1 = Steam
                'search': game_title,
                'page_size': 5
            }
            response = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check if any result has matching Steam AppID in stores
            for result in data.get('results', []):
                game_id = result['id']
                # Fetch detailed info to check Steam store
                details = fetch_rawg_game_details(game_id)
                if details and 'stores' in details:
                    for store in details.get('stores', []):
                        if store.get('store', {}).get('id') == 1:  # Steam store
                            store_url = store.get('url', '')
                            if f'/{steam_appid}' in store_url or f'app/{steam_appid}' in store_url:
                                logger.info(f"Found exact Steam match for {game_title} (AppID: {steam_appid})")
                                return game_id
        except requests.RequestException as e:
            logger.error(f"Error searching by Steam AppID for {game_title}: {e}")

    # Strategy 2: Precise title search
    params = {
        'key': RAWG_API_KEY,
        'search': game_title,
        'search_precise': True,
        'page_size': 1
    }
    try:
        response = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('results'):
            game_id = data['results'][0]['id']
            logger.info(f"Found RAWG game for '{game_title}': ID {game_id}")
            return game_id
        else:
            logger.warning(f"No RAWG results found for '{game_title}'")
    except requests.RequestException as e:
        logger.error(f"Error searching for game '{game_title}': {e}")
    
    return None

def fetch_rawg_game_details(game_id):
    """
    Fetch detailed game information from RAWG.
    """
    if not RAWG_API_KEY:
        return None

    try:
        response = requests.get(
            f"{BASE_URL}/games/{game_id}", 
            params={'key': RAWG_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching details for RAWG game {game_id}: {e}")
        return None

def fetch_rawg_screenshots(game_id, limit=10):
    """
    Fetch screenshots from RAWG.
    """
    if not RAWG_API_KEY:
        return []

    try:
        params = {
            'key': RAWG_API_KEY,
            'page_size': limit
        }
        response = requests.get(
            f"{BASE_URL}/games/{game_id}/screenshots", 
            params=params,
            timeout=10
        )
        response.raise_for_status()
        results = response.json().get('results', [])
        logger.info(f"Fetched {len(results)} screenshots for RAWG game {game_id}")
        return results
    except requests.RequestException as e:
        logger.error(f"Error fetching screenshots for RAWG game {game_id}: {e}")
        return []

def fetch_rawg_trailers(game_id):
    """
    Fetch trailers/movies from RAWG.
    """
    if not RAWG_API_KEY:
        return []

    try:
        response = requests.get(
            f"{BASE_URL}/games/{game_id}/movies", 
            params={'key': RAWG_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        results = response.json().get('results', [])
        logger.info(f"Fetched {len(results)} trailers for RAWG game {game_id}")
        return results
    except requests.RequestException as e:
        logger.error(f"Error fetching trailers for RAWG game {game_id}: {e}")
        return []

def translate_text_gemini(text):
    """
    Translate text using Gemini API (or other available method).
    """
    api_key = os.getenv('GMS_API_KEY')
    if not api_key:
        logger.warning("GMS_API_KEY for translation not configured")
        return None

    try:
        prompt = f"""당신은 10년 경력의 전문 게임 로컬라이제이션 번역가입니다. 
게임의 재미와 분위기를 살려서 자연스러운 한국어로 번역해주세요.

규칙:
1. 고유명사(타이틀, 캐릭터 등)는 필요시 원어 병기 또는 통용되는 표기 사용
2. 게임 용어(로그라이크, 오픈월드 등)는 한국 게이머들에게 익숙한 표현 사용
3. 번역투를 피하고 자연스러운 한국어 문장으로 의역
4. 오직 번역된 텍스트만 출력하세요. 설명이나 잡담 금지.

원문:
{text}

한국어 번역:"""

        response = requests.post(
            f"https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            candidates = result.get('candidates', [])
            if candidates:
                translation = candidates[0]['content']['parts'][0]['text'].strip()
                return translation
        else:
            logger.error(f"Gemini translation failed: {response.status_code} {response.text}")
            
    except Exception as e:
        logger.error(f"Error calling Gemini translation API: {e}")
        
    return None

def update_game_with_rawg(game, force_refresh=False):
    """
    Update a Game instance with enriched data from RAWG API.
    
    Args:
        game: Game instance to update
        force_refresh: If True, fetch data even if already exists
    
    Returns:
        bool: True if successfully updated, False otherwise
    """
    if not RAWG_API_KEY:
        logger.warning("Cannot update game - RAWG_API_KEY not configured")
        return False
    
    # Check if update is needed
    if not force_refresh and game.rawg_id and game.description and game.background_image:
        logger.debug(f"Game '{game.title}' already has RAWG data, skipping.")
        return True
    
    # Get or find RAWG ID
    if game.rawg_id:
        rawg_id = game.rawg_id
        logger.info(f"Using existing RAWG ID {rawg_id} for '{game.title}'")
    else:
        rawg_id = get_rawg_game_id(game.title, steam_appid=game.steam_appid)
        if not rawg_id:
            logger.warning(f"Could not find RAWG ID for '{game.title}'")
            return False
        game.rawg_id = rawg_id
        game.save(update_fields=['rawg_id'])
        logger.info(f"Saved RAWG ID {rawg_id} for '{game.title}'")

    # Fetch and update game details
    details = fetch_rawg_game_details(rawg_id)
    if details:
        # Update description (prefer raw text over HTML)
        description = details.get('description_raw', '') or details.get('description', '')
        if description:
            game.description = description
        
        # Update background image (high quality poster)
        background_image = details.get('background_image', '')
        if background_image:
            game.background_image = background_image
        
        # Update metacritic score
        metacritic_score = details.get('metacritic')
        if metacritic_score:
            game.metacritic_score = metacritic_score
        
        # Update genre if still default/empty
        if game.genre in ['Unknown', '게임', ''] and details.get('genres'):
            genres = [g['name'] for g in details['genres'][:3]]  # Top 3 genres
            game.genre = ', '.join(genres)
        
        game.save()
        logger.info(f"Updated game details for '{game.title}'")
        
        # Update tags (genres + tags from RAWG)
        tags_added = 0
        
        # Add genre tags
        for genre_data in details.get('genres', []):
            tag, created = Tag.objects.get_or_create(
                slug=genre_data['slug'],
                defaults={
                    'name': genre_data['name'],
                    'tag_type': 'genre',
                    'weight': 1.0
                }
            )
            if tag not in game.tags.all():
                game.tags.add(tag)
                tags_added += 1
        
        # Add detailed tags (only English)
        for tag_data in details.get('tags', []):
            if tag_data.get('language', 'eng') != 'eng':
                continue
            tag_type = get_tag_type(tag_data['slug'])
            tag, created = Tag.objects.get_or_create(
                slug=tag_data['slug'],
                defaults={
                    'name': tag_data['name'],
                    'tag_type': tag_type,
                    'weight': 1.0
                }
            )
            if tag not in game.tags.all():
                game.tags.add(tag)
                tags_added += 1
        
        if tags_added > 0:
            logger.info(f"Added {tags_added} tags for '{game.title}'")
    else:
        logger.warning(f"Could not fetch details for RAWG game {rawg_id}")
        return False

    # Fetch and save screenshots (avoid duplicates)
    screenshots = fetch_rawg_screenshots(rawg_id, limit=10)
    screenshot_count = 0
    for ss in screenshots:
        _, created = GameScreenshot.objects.get_or_create(
            game=game,
            image_url=ss['image']
        )
        if created:
            screenshot_count += 1
    
    if screenshot_count > 0:
        logger.info(f"Added {screenshot_count} new screenshots for '{game.title}'")

    # Fetch and save trailers (avoid duplicates)
    trailers = fetch_rawg_trailers(rawg_id)
    trailer_count = 0
    for tr in trailers:
        # Check if trailer data has required fields
        if 'data' not in tr or '480' not in tr['data'] or 'max' not in tr['data']:
            logger.warning(f"Skipping trailer '{tr.get('name', 'Unknown')}' - missing video data")
            continue
            
        _, created = GameTrailer.objects.get_or_create(
            game=game,
            name=tr['name'],
            defaults={
                'preview_url': tr.get('preview', ''),
                'data_480': tr['data']['480'],
                'data_max': tr['data']['max']
            }
        )
        if created:
            trailer_count += 1
    
    if trailer_count > 0:
        logger.info(f"Added {trailer_count} new trailers for '{game.title}'")

    logger.info(f"Successfully updated RAWG data for '{game.title}'")
    return True


# ============================================================================
# B. 게임 검색 및 매핑
# ============================================================================

def search_games(query, platforms='4', page_size=20):
    """
    Search for games on RAWG by title.
    
    Args:
        query: Game title to search for
        platforms: Platform ID (4 = PC, default)
        page_size: Number of results to return (default: 20)
    
    Returns:
        list: List of game dictionaries with basic info
    """
    if not RAWG_API_KEY:
        logger.warning("RAWG_API_KEY not configured")
        return []
    
    try:
        params = {
            'key': RAWG_API_KEY,
            'search': query,
            'platforms': platforms,
            'page_size': page_size
        }
        response = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for game in data.get('results', []):
            results.append({
                'rawg_id': game['id'],
                'title': game['name'],
                'image_url': game.get('background_image', ''),
                'rating': game.get('rating'),
                'released': game.get('released'),
                'genres': [g['name'] for g in game.get('genres', [])],
                'metacritic': game.get('metacritic')
            })
        
        logger.info(f"Found {len(results)} games for query '{query}'")
        return results
    
    except requests.RequestException as e:
        logger.error(f"Error searching games for '{query}': {e}")
        return []


# ============================================================================
# C. 분류 및 태그 (UI 필터용)
# ============================================================================

def get_genres(page_size=50):
    """
    Get list of all game genres from RAWG.
    
    Returns:
        list: List of genre dictionaries with id, name, slug, and image
    """
    if not RAWG_API_KEY:
        logger.warning("RAWG_API_KEY not configured")
        return []
    
    try:
        params = {
            'key': RAWG_API_KEY,
            'page_size': page_size
        }
        response = requests.get(f"{BASE_URL}/genres", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        genres = []
        for genre in data.get('results', []):
            genres.append({
                'id': genre['id'],
                'name': genre['name'],
                'slug': genre['slug'],
                'games_count': genre.get('games_count', 0),
                'image_background': genre.get('image_background', '')
            })
        
        logger.info(f"Fetched {len(genres)} genres from RAWG")
        return genres
    
    except requests.RequestException as e:
        logger.error(f"Error fetching genres: {e}")
        return []


def get_platforms(page_size=50):
    """
    Get list of all gaming platforms from RAWG.
    
    Returns:
        list: List of platform dictionaries with id, name, and slug
    """
    if not RAWG_API_KEY:
        logger.warning("RAWG_API_KEY not configured")
        return []
    
    try:
        params = {
            'key': RAWG_API_KEY,
            'page_size': page_size
        }
        response = requests.get(f"{BASE_URL}/platforms", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        platforms = []
        for platform in data.get('results', []):
            platforms.append({
                'id': platform['id'],
                'name': platform['name'],
                'slug': platform['slug'],
                'games_count': platform.get('games_count', 0),
                'image_background': platform.get('image_background', '')
            })
        
        logger.info(f"Fetched {len(platforms)} platforms from RAWG")
        return platforms
    
    except requests.RequestException as e:
        logger.error(f"Error fetching platforms: {e}")
        return []


def get_games_by_genre(genre_slug, page_size=20):
    """
    Get games filtered by genre.
    
    Args:
        genre_slug: Genre slug (e.g., 'action', 'rpg', 'strategy')
        page_size: Number of results to return
    
    Returns:
        list: List of games in that genre
    """
    if not RAWG_API_KEY:
        logger.warning("RAWG_API_KEY not configured")
        return []
    
    try:
        params = {
            'key': RAWG_API_KEY,
            'genres': genre_slug,
            'page_size': page_size,
            'platforms': '4'  # PC only
        }
        response = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for game in data.get('results', []):
            results.append({
                'rawg_id': game['id'],
                'title': game['name'],
                'image_url': game.get('background_image', ''),
                'rating': game.get('rating'),
                'genres': [g['name'] for g in game.get('genres', [])],
                'metacritic': game.get('metacritic')
            })
        
        logger.info(f"Found {len(results)} games for genre '{genre_slug}'")
        return results
    
    except requests.RequestException as e:
        logger.error(f"Error fetching games by genre '{genre_slug}': {e}")
        return []


# ============================================================================
# D. 인기순/정렬 기능 ('요즘 뜨는 게임' 섹션용)
# ============================================================================

def get_games_by_ordering(ordering='-added', page_size=20, platforms='4', 
                           ratings_count_min=None, added_min=None, 
                           metacritic_min=None, exclude_additions=True):
    """
    Get games sorted by various criteria with quality filters.
    
    Args:
        ordering: Sorting option (default: '-added' for most popular)
            Available options:
            - '-added': Most added to libraries (인기순)
            - '-rating': Highest rated (평점 높은 순)
            - '-metacritic': Highest metacritic score (메타크리틱 높은 순)
            - '-released': Recently released (최신 출시순)
            - 'name': Alphabetical order (가나다순)
            - '-created': Recently created (최근 생성순)
            - '-updated': Recently updated (최근 업데이트순)
        page_size: Number of results to return
        platforms: Platform ID (4 = PC, default)
        ratings_count_min: Minimum number of ratings (filters low-sample games)
        added_min: Minimum number of users who added (filters obscure games)
        metacritic_min: Minimum metacritic score
        exclude_additions: Exclude DLCs and additions (default: True)
    
    Returns:
        list: List of games sorted by the specified criteria
    """
    if not RAWG_API_KEY:
        logger.warning("RAWG_API_KEY not configured")
        return []
    
    try:
        params = {
            'key': RAWG_API_KEY,
            'ordering': ordering,
            'page_size': page_size,
            'platforms': platforms
        }
        
        # Quality filters
        if ratings_count_min:
            # Request more games to filter client-side, as RAWG doesn't support
            # direct ratings_count filtering, we'll filter after receiving
            params['page_size'] = page_size * 3  # Get more to filter
        
        if added_min:
            # Added count filter (number of users who added game to library)
            # RAWG doesn't support this directly, so we filter after
            params['page_size'] = max(params['page_size'], page_size * 3)
        
        if metacritic_min:
            # Metacritic filter - RAWG supports this!
            params['metacritic'] = f"{metacritic_min},100"
        
        if exclude_additions:
            params['exclude_additions'] = 'true'
        
        response = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for game in data.get('results', []):
            # Apply client-side filters
            ratings_count = game.get('ratings_count', 0)
            added_count = game.get('added', 0)
            
            # Filter by ratings_count (minimum reviews)
            if ratings_count_min and ratings_count < ratings_count_min:
                continue
            
            # Filter by added count (minimum library additions)
            if added_min and added_count < added_min:
                continue
            
            results.append({
                'rawg_id': game['id'],
                'slug': game.get('slug', ''),
                'title': game['name'],
                'image_url': game.get('background_image', ''),
                'rating': game.get('rating'),
                'ratings_count': ratings_count,
                'released': game.get('released'),
                'genres': [g['name'] for g in game.get('genres', [])],
                'metacritic': game.get('metacritic'),
                'added': added_count
            })
            
            # Stop when we have enough results
            if len(results) >= page_size:
                break
        
        logger.info(f"Fetched {len(results)} games with ordering '{ordering}' (filtered)")
        return results
    
    except requests.RequestException as e:
        logger.error(f"Error fetching games with ordering '{ordering}': {e}")
        return []


def get_popular_games(page_size=20, all_time=False):
    """
    Get most popular games.
    
    Args:
        page_size: Number of results (default: 20)
        all_time: If True, get all-time popular games without date filter
                  If False, get popular games from last 2 years only
    
    Returns:
        list: Most popular games
    """
    if not RAWG_API_KEY:
        logger.warning("RAWG_API_KEY not configured")
        return []
    
    try:
        params = {
            'key': RAWG_API_KEY,
            'ordering': '-added',  # Most added to libraries
            'page_size': page_size * 3,  # Get more to filter
            'platforms': '4',  # PC only
            'exclude_additions': 'true'  # Exclude DLCs
        }
        
        # Apply date filter only if not all_time
        if not all_time:
            from datetime import datetime, timedelta
            today = datetime.now().strftime('%Y-%m-%d')
            two_years_ago = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
            params['dates'] = f'{two_years_ago},{today}'  # Games from last 2 years
        
        response = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for game in data.get('results', []):
            # Quality filter: at least 100 users added (relaxed)
            added_count = game.get('added', 0)
            if added_count < 100:
                continue
            
            results.append({
                'rawg_id': game['id'],
                'slug': game.get('slug', ''),
                'title': game['name'],
                'image_url': game.get('background_image', ''),
                'rating': game.get('rating'),
                'ratings_count': game.get('ratings_count', 0),
                'released': game.get('released'),
                'genres': [g['name'] for g in game.get('genres', [])],
                'metacritic': game.get('metacritic'),
                'added': added_count
            })
            
            if len(results) >= page_size:
                break
        
        logger.info(f"Fetched {len(results)} popular games (all_time={all_time})")
        return results
    
    except requests.RequestException as e:
        logger.error(f"Error fetching popular games: {e}")
        return []


def get_top_rated_games(page_size=20):
    """
    Get most popular games sorted by popularity (added count).
    Only games with added >= 100, with scam filtering.
    
    Args:
        page_size: Number of results (default: 20)
    
    Returns:
        list: Most popular games with scam filter
    """
    if not RAWG_API_KEY:
        logger.warning("RAWG_API_KEY not configured")
        return []
    
    # Blacklist for scam games
    BLACKLIST_PATTERNS = [
        'hot ', 'sexy ', 'nude', 'naked', 'hentai', 'porn', 'adult', 
        'bikini', 'busty', 'boob', 'tits', 'ass ', 'tentacle', 'waifu'
    ]
    
    try:
        params = {
            'key': RAWG_API_KEY,
            'ordering': '-added',  # Popularity (most added to libraries)
            'page_size': page_size * 3,  # Get more to filter
            'platforms': '4',
            'exclude_additions': 'true'
        }
        response = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for game in data.get('results', []):
            title = game.get('name', '').lower()
            added_count = game.get('added', 0)
            image_url = game.get('background_image', '')
            
            # Must be popular (at least 500 added)
            if added_count < 100:
                continue
            
            # Must have image
            if not image_url:
                continue
            
            # Scam filter
            is_blacklisted = False
            for pattern in BLACKLIST_PATTERNS:
                if pattern in title:
                    is_blacklisted = True
                    break
            if is_blacklisted:
                continue
            
            results.append({
                'rawg_id': game['id'],
                'slug': game.get('slug', ''),
                'title': game['name'],
                'image_url': image_url,
                'rating': game.get('rating'),
                'ratings_count': game.get('ratings_count', 0),
                'released': game.get('released'),
                'genres': [g['name'] for g in game.get('genres', [])],
                'metacritic': game.get('metacritic'),
                'added': added_count
            })
            
            if len(results) >= page_size:
                break
        
        # Sort by rating (highest first) among popular games
        results.sort(key=lambda x: x.get('rating') or 0, reverse=True)
        
        logger.info(f"Fetched {len(results)} popular games sorted by rating")
        return results
    
    except requests.RequestException as e:
        logger.error(f"Error fetching top rated games: {e}")
        return []


def get_trending_games(page_size=20):
    """
    Get games with highest metacritic scores.
    Only includes games with metacritic score of 70+.
    
    Args:
        page_size: Number of results (default: 20)
    
    Returns:
        list: Games sorted by metacritic score (70+)
    """
    return get_games_by_ordering(
        ordering='-metacritic', 
        page_size=page_size,
        metacritic_min=70  # Only games with 70+ metacritic
    )


def get_new_releases(page_size=20):
    """
    Get recently released games (already released, not upcoming).
    Includes quality filtering to remove scam/low-quality games.
    
    Args:
        page_size: Number of results (default: 20)
    
    Returns:
        list: Recently released games (past 1 year, with minimal scam filters)
    """
    if not RAWG_API_KEY:
        logger.warning("RAWG_API_KEY not configured")
        return []
    
    # Blacklist for obvious scam game title patterns (minimal)
    BLACKLIST_PATTERNS = [
        'hot ', 'sexy ', 'nude', 'naked', 'hentai', 'porn', 'adult', 
        'bikini', 'busty', 'boob', 'tits', 'ass '
    ]
    
    try:
        from datetime import datetime, timedelta
        today = datetime.now().strftime('%Y-%m-%d')
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        params = {
            'key': RAWG_API_KEY,
            'dates': f'{one_year_ago},{today}',  # Last 1 year
            'ordering': '-released',  # Most recent first
            'page_size': page_size * 4,  # Get more to filter scams
            'platforms': '4',  # PC only
            'exclude_additions': 'true'  # Exclude DLCs
        }
        response = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for game in data.get('results', []):
            # --- Scam/Quality Filters ---
            title = game.get('name', '').lower()
            added_count = game.get('added', 0)
            ratings_count = game.get('ratings_count', 0)
            image_url = game.get('background_image', '')
            
            # 1. Must have an image (scam games often don't)
            if not image_url:
                continue
            
            # 2. Must have at least 3 users who added it (very relaxed)
            if added_count < 3:
                continue
            
            # 3. Check against blacklist patterns
            is_blacklisted = False
            for pattern in BLACKLIST_PATTERNS:
                if pattern in title:
                    is_blacklisted = True
                    break
            if is_blacklisted:
                logger.debug(f"Filtered scam game: {game.get('name')}")
                continue
            
            # 4. Prefer games with at least some ratings (more trustworthy)
            # But don't require it for brand new games
            
            results.append({
                'rawg_id': game['id'],
                'slug': game.get('slug', ''),
                'title': game['name'],
                'image_url': image_url,
                'rating': game.get('rating'),
                'ratings_count': ratings_count,
                'released': game.get('released'),
                'genres': [g['name'] for g in game.get('genres', [])],
                'metacritic': game.get('metacritic'),
                'added': added_count
            })
            
            if len(results) >= page_size:
                break
        
        logger.info(f"Fetched {len(results)} new releases (filtered for quality)")
        return results
    
    except requests.RequestException as e:
        logger.error(f"Error fetching new releases: {e}")
        return []


def get_upcoming_games(page_size=20):
    """
    Get upcoming games (to be released).
    
    Args:
        page_size: Number of results (default: 20)
    
    Returns:
        list: Upcoming games
    """
    if not RAWG_API_KEY:
        logger.warning("RAWG_API_KEY not configured")
        return []
    
    try:
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'key': RAWG_API_KEY,
            'dates': f'{today},2026-12-31',  # From today to future
            'ordering': 'released',  # Soonest first
            'page_size': page_size,
            'platforms': '4'  # PC only
        }
        response = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for game in data.get('results', []):
            results.append({
                'rawg_id': game['id'],
                'title': game['name'],
                'image_url': game.get('background_image', ''),
                'rating': game.get('rating'),
                'released': game.get('released'),
                'genres': [g['name'] for g in game.get('genres', [])],
                'metacritic': game.get('metacritic')
            })
        
        logger.info(f"Fetched {len(results)} upcoming games")
        return results
    
    except requests.RequestException as e:
        logger.error(f"Error fetching upcoming games: {e}")
        return []
