"""
Game Recommendation Engine - Optimized Version
Based on Steam library, ratings, and sales data
"""
import os
import requests
import logging
from collections import Counter
from pathlib import Path
from django.conf import settings as django_settings

logger = logging.getLogger(__name__)

def get_rawg_api_key():
    """
    Get RAWG API key from environment or Django settings
    This ensures the key is loaded correctly in all contexts
    """
    # First try from environment (already loaded by Django settings)
    key = os.getenv('RAWG_API_KEY')
    
    if not key:
        # Try loading .env explicitly as fallback
        try:
            from dotenv import load_dotenv
            BASE_DIR = Path(__file__).resolve().parent.parent
            load_dotenv(BASE_DIR / '.env')
            key = os.getenv('RAWG_API_KEY')
        except Exception as e:
            logger.error(f"Error loading .env: {e}")
    
    return key

# For backward compatibility, also set module-level variable
RAWG_API_KEY = get_rawg_api_key()
print(f"[DEBUG] Module load - RAWG_API_KEY: {bool(RAWG_API_KEY)}, length: {len(RAWG_API_KEY) if RAWG_API_KEY else 0}")

BASE_URL = "https://api.rawg.io/api"

# Pre-defined genre mapping for common games (no API calls needed)
COMMON_GAME_GENRES = {
    'dota': ['action', 'strategy'],
    'counter-strike': ['shooter', 'action'],
    'pubg': ['shooter', 'action'],
    'apex': ['shooter', 'action'],
    'valorant': ['shooter', 'action'],
    'overwatch': ['shooter', 'action'],
    'league of legends': ['strategy', 'action'],
    'stardew': ['simulation', 'indie', 'rpg'],
    'terraria': ['action', 'indie', 'adventure'],
    'minecraft': ['adventure', 'simulation'],
    'witcher': ['rpg', 'action', 'adventure'],
    'skyrim': ['rpg', 'action', 'adventure'],
    'dark souls': ['rpg', 'action'],
    'elden ring': ['rpg', 'action'],
    'gta': ['action', 'adventure'],
    'red dead': ['action', 'adventure'],
    'cyberpunk': ['rpg', 'action'],
    'fallout': ['rpg', 'action'],
    'civilization': ['strategy', 'simulation'],
    'total war': ['strategy'],
    'europa universalis': ['strategy', 'simulation'],
    'crusader kings': ['strategy', 'simulation'],
    'cities skylines': ['simulation', 'strategy'],
    'planet coaster': ['simulation'],
    'satisfactory': ['simulation', 'strategy'],
    'factorio': ['simulation', 'strategy', 'indie'],
    'rimworld': ['simulation', 'strategy', 'indie'],
    'hollow knight': ['action', 'indie', 'platformer'],
    'celeste': ['indie', 'platformer'],
    'hades': ['action', 'indie', 'rpg'],
    'dead cells': ['action', 'indie'],
    'risk of rain': ['action', 'indie'],
    'monster hunter': ['action', 'rpg'],
    'destiny': ['shooter', 'action'],
    'warframe': ['shooter', 'action'],
    'path of exile': ['rpg', 'action'],
    'diablo': ['rpg', 'action'],
    'borderlands': ['shooter', 'action', 'rpg'],
    'mount': ['rpg', 'action', 'strategy'],  # Mount & Blade
    'arma': ['shooter', 'simulation'],
    'rust': ['action', 'adventure', 'indie'],
    'ark': ['action', 'adventure'],
    'subnautica': ['adventure', 'indie'],
    'no man': ['adventure', 'simulation'],
    'elite dangerous': ['simulation', 'action'],
    'football manager': ['simulation', 'sports'],
    'fifa': ['sports', 'simulation'],
    'nba': ['sports', 'simulation'],
    'racing': ['racing', 'simulation'],
    'forza': ['racing', 'simulation'],
    'assetto': ['racing', 'simulation'],
    'project cars': ['racing', 'simulation'],
    'resident evil': ['action', 'adventure'],
    'silent hill': ['adventure', 'puzzle'],
    'amnesia': ['adventure', 'indie'],
    'outlast': ['adventure', 'indie'],
    'phasmophobia': ['indie', 'simulation'],
    'among us': ['indie', 'casual'],
    'fall guys': ['casual', 'action'],
    'rocket league': ['sports', 'racing'],
}


def get_genres_from_game_name(game_name):
    """
    Get genres from game name using pre-defined mapping
    Fast - no API calls!
    """
    name_lower = game_name.lower()
    
    for keyword, genres in COMMON_GAME_GENRES.items():
        if keyword in name_lower:
            return genres
    
    # Default genres for unknown games
    return ['action']


def analyze_library_genres_fast(steam_library, limit=5):
    """
    Fast genre analysis using only game names
    No API calls - instant!
    
    Args:
        steam_library: List of Steam games with 'name' and 'playtime_forever'
        limit: Number of top games to analyze
    
    Returns:
        Counter: Genre frequency counter
    """
    # Sort by playtime and get top games
    top_games = sorted(
        steam_library, 
        key=lambda x: x.get('playtime_forever', 0), 
        reverse=True
    )[:limit]
    
    genre_counter = Counter()
    
    for game in top_games:
        name = game.get('name', '')
        genres = get_genres_from_game_name(name)
        for genre in genres:
            # Weight by playtime (more playtime = more important)
            playtime_weight = min(game.get('playtime_forever', 0) / 60, 100)  # Cap at 100 hours
            genre_counter[genre] += max(1, int(playtime_weight / 10))
    
    return genre_counter


def get_recommendations_by_genres(genres, limit=250, max_pages=1):
    """
    Get game recommendations based on genre list - ULTRA FAST VERSION
    
    Optimized: Only 3 API calls total (down from 112!)
    - 1 call per ordering type: -rating, -added, -metacritic
    - Each returns 40 games = 120 unique games max
    
    Args:
        genres: List of genre slugs
        limit: Maximum number of results (default 250)
        max_pages: Pages per ordering (default 1 for speed)
    
    Returns:
        list: Recommended games
    """
    # Get API key at call time to ensure it's loaded
    api_key = get_rawg_api_key()
    
    print(f"[DEBUG] get_recommendations_by_genres called with genres: {genres}, limit: {limit}")
    print(f"[DEBUG] RAWG_API_KEY exists: {bool(api_key)}")
    
    if not api_key or not genres:
        print(f"[DEBUG] Early return - API key or genres missing")
        return []
    
    all_results = []
    seen_ids = set()  # Avoid duplicates
    
    # Use top 2 genres for best match
    genre_string = ','.join(genres[:2]) if len(genres) >= 2 else genres[0]
    
    # Only 3 orderings for speed (metacritic first for quality!)
    orderings = ['-metacritic', '-rating', '-added']
    
    try:
        for ordering in orderings:
            if len(all_results) >= limit:
                break
            
            params = {
                'key': api_key,
                'genres': genre_string,
                'ordering': ordering,
                'page_size': 40,  # Max allowed by RAWG
                'page': 1,
                'platforms': '4',  # PC
                'metacritic': '60,100',  # Only quality games
            }
            
            print(f"[DEBUG] Fetching: genres={genre_string}, ordering={ordering}")
            response = requests.get(f"{BASE_URL}/games", params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for game in data.get('results', []):
                    # Skip duplicates
                    if game['id'] in seen_ids:
                        continue
                    seen_ids.add(game['id'])
                    
                    all_results.append({
                        'rawg_id': game['id'],
                        'title': game['name'],
                        'image_url': game.get('background_image', ''),
                        'rating': game.get('rating', 0),
                        'ratings_count': game.get('ratings_count', 0),
                        'metacritic': game.get('metacritic'),
                        'released': game.get('released'),
                        'genres': [g['name'] for g in game.get('genres', [])],
                        'added': game.get('added', 0),
                    })
                    
                    if len(all_results) >= limit:
                        break
            else:
                print(f"[DEBUG] RAWG API error: {response.status_code}")
                        
        print(f"[DEBUG] Total fetched: {len(all_results)} recommendations (FAST mode)")
        logger.info(f"Fetched {len(all_results)} recommendations for genres: {genres}")
        return all_results
            
    except requests.RequestException as e:
        print(f"[DEBUG] RAWG API request exception: {e}")
        logger.error(f"Error fetching recommendations: {e}")
    
    return all_results


def calculate_recommendation_score(game, user_genres, is_on_sale=False, sale_discount=0):
    """
    Calculate recommendation score (0-100)
    
    Priority (updated):
    1. Genre match: 40 points max
    2. Metacritic score: 25 points max (NEW - higher than sale!)
    3. Rating: 20 points max
    4. Sale bonus: 15 points max
    """
    score = 0
    
    # 1. Genre match (40 points max)
    game_genres = [g.lower().replace(' ', '-') for g in game.get('genres', [])]
    if user_genres:
        genre_matches = sum(user_genres.get(g, 0) for g in game_genres)
        max_genre_score = max(user_genres.values()) if user_genres else 1
        genre_score = min(40, (genre_matches / max(max_genre_score, 1)) * 40)
        score += genre_score
    
    # 2. Metacritic score (25 points max) - HIGHER PRIORITY THAN SALE
    metacritic = game.get('metacritic') or 0
    if metacritic > 0:
        # Scale: 60-100 metacritic → 0-25 points
        metacritic_score = min(25, max(0, (metacritic - 60) / 40 * 25))
        score += metacritic_score
    
    # 3. Rating (20 points max)
    rating = game.get('rating', 0) or 0
    rating_score = (rating / 5) * 20
    score += rating_score
    
    # 4. Sale bonus (15 points max) - Lower priority than metacritic
    if is_on_sale:
        sale_score = min(15, (sale_discount / 100) * 15)
        score += sale_score
    
    return round(score, 1)


def get_personalized_recommendations(steam_library, sale_games=None, limit=50):
    """
    Generate personalized recommendations - FAST VERSION
    
    Algorithm:
    1. Analyze top 5 games by playtime (instant - no API)
    2. Extract genres from game names (instant - no API)
    3. Single RAWG API call for recommendations
    4. Filter out already owned games
    5. Calculate scores and sort
    
    Total: 3 API calls only!
    """
    if not steam_library:
        return {
            'recommendations': [],
            'genres_analysis': {},
            'is_personalized': False,
            'message': 'Steam 라이브러리가 없습니다. Steam을 연동해주세요.'
        }
    
    sale_games = sale_games or []
    
    # Step 0: Build owned games set for exclusion (normalize titles)
    owned_games = set()
    for game in steam_library:
        name = game.get('name', '').lower()
        # Normalize: remove special chars, editions, etc.
        normalized = name.replace(':', '').replace('-', ' ').replace('®', '').replace('™', '')
        normalized = ' '.join(normalized.split())  # Collapse whitespace
        owned_games.add(normalized)
        
        # Also add short version (first significant words)
        words = normalized.split()
        if len(words) >= 2:
            owned_games.add(' '.join(words[:2]))  # First 2 words
        if len(words) >= 3:
            owned_games.add(' '.join(words[:3]))  # First 3 words
    
    print(f"[DEBUG] Owned games count: {len(owned_games)}, sample: {list(owned_games)[:5]}")
    
    # Step 1: Fast genre analysis (NO API CALLS)
    user_genres = analyze_library_genres_fast(steam_library, limit=5)
    
    if not user_genres:
        return {
            'recommendations': [],
            'genres_analysis': {},
            'is_personalized': False,
            'message': '장르 분석에 실패했습니다.'
        }
    
    # Get top genres
    top_genres = [g for g, _ in user_genres.most_common(3)]
    
    # Step 2: Get recommendations (3 API CALLS - fetch more to filter)
    # Request 3x limit to have enough after filtering owned games
    recommended_games = get_recommendations_by_genres(top_genres, limit=limit * 3)
    
    if not recommended_games:
        return {
            'recommendations': [],
            'genres_analysis': {
                'top_genres': [{'name': g, 'count': c} for g, c in user_genres.most_common(5)],
            },
            'is_personalized': True,
            'message': f"'{top_genres[0]}' 장르를 좋아하시네요! 하지만 추천 게임을 가져오지 못했습니다."
        }
    
    # Step 3: Filter out already owned games
    def is_owned(game_title):
        title_lower = game_title.lower()
        normalized = title_lower.replace(':', '').replace('-', ' ').replace('®', '').replace('™', '')
        normalized = ' '.join(normalized.split())
        
        # Check exact match
        if normalized in owned_games:
            return True
        
        # Check short version match
        words = normalized.split()
        if len(words) >= 2 and ' '.join(words[:2]) in owned_games:
            return True
        if len(words) >= 3 and ' '.join(words[:3]) in owned_games:
            return True
        
        # Check if any owned game name is contained in this title or vice versa
        for owned in owned_games:
            if len(owned) > 5:  # Only check meaningful names
                if owned in normalized or normalized in owned:
                    return True
        
        return False
    
    filtered_games = []
    excluded_count = 0
    for game in recommended_games:
        if is_owned(game['title']):
            excluded_count += 1
            print(f"[DEBUG] Excluding owned game: {game['title']}")
        else:
            filtered_games.append(game)
    
    print(f"[DEBUG] Filtered {excluded_count} owned games, {len(filtered_games)} remaining")
    
    # Step 4: Create sale lookup
    sale_lookup = {}
    for sale_game in sale_games:
        title_lower = sale_game.get('title', '').lower()
        # Handle None values safely
        discount_rate = sale_game.get('discount_rate') or 0
        current_price = sale_game.get('current_price') or 0
        original_price = sale_game.get('original_price') or 0
        
        sale_lookup[title_lower] = {
            'discount': discount_rate * 100,
            'current_price': current_price,
            'original_price': original_price,
        }
    
    # Step 5: Calculate scores for filtered games (not owned)
    for game in filtered_games:
        title_lower = game['title'].lower()
        sale_info = sale_lookup.get(title_lower, {})
        is_on_sale = bool(sale_info)
        discount = sale_info.get('discount', 0)
        
        game['recommendation_score'] = calculate_recommendation_score(
            game, user_genres, is_on_sale, discount
        )
        game['is_on_sale'] = is_on_sale
        if is_on_sale:
            game['discount_rate'] = discount
            game['current_price'] = sale_info.get('current_price')
            game['original_price'] = sale_info.get('original_price')
    
    # Sort by score
    filtered_games.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)
    
    # Get genre for display
    top_genre_display = top_genres[0].replace('-', ' ').title()
    
    return {
        'recommendations': filtered_games[:limit],
        'genres_analysis': {
            'top_genres': [{'name': g.replace('-', ' ').title(), 'count': c} for g, c in user_genres.most_common(5)],
            'total_genres': len(user_genres),
        },
        'is_personalized': True,
        'message': f"'{top_genre_display}' 장르를 좋아하시네요! 비슷한 게임을 추천해드립니다."
    }

