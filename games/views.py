from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from .models import Game, Rating, CachedGameList, SteamReview
from users.models import GameRating  # 실제 유저 평가 데이터
from .utils import (
    update_game_with_rawg, 
    search_games, 
    get_genres, 
    get_platforms,
    get_games_by_genre,
    get_popular_games,
    get_top_rated_games,
    get_trending_games,
    get_new_releases,
    get_upcoming_games,
    get_games_by_ordering,
    fetch_rawg_game_details,
    fetch_rawg_screenshots,
    RAWG_API_KEY
)
import re
import os

def extract_app_id(game_id_str):
    """Extract numeric app ID from Steam game_id (e.g., 'app1234', 'bundle5678')"""
    # game_id_str could be 'app2576020', 'bundle5926', 'sub516201', or just '1234'
    match = re.search(r'\d+', str(game_id_str))
    if match:
        return int(match.group())
    return int(game_id_str)  # fallback for pure numbers

def is_steam_id(game_id_str):
    """Check if game_id is a Steam format (app123, bundle456, sub789)"""
    return str(game_id_str).startswith(('app', 'bundle', 'sub'))

@login_required
def game_search_by_title(request):
    """
    제목으로 게임 검색 후 상세 페이지로 리다이렉트
    
    세일 탭에서 Steam AppID와 RAWG ID가 다른 게임 처리용
    RAWG API에서 제목으로 검색 후 게임을 DB에 저장하고 상세페이지로 이동
    
    Query params:
        title (required): 검색할 게임 제목
        steam_appid (optional): Steam AppID (가격 비교 링크용)
    """
    title = request.GET.get('title', '').strip()
    steam_appid = request.GET.get('steam_appid', '')
    rawg_id_param = request.GET.get('rawg_id', '')
    
    print(f"[DEBUG] game_search_by_title called: title='{title}', steam_appid={steam_appid}, rawg_id={rawg_id_param}")
    
    if not title:
        print("[DEBUG] No title provided, redirecting to main")
        return redirect('users:main')
    
    # rawg_id가 직접 제공된 경우 바로 상세페이지로
    if rawg_id_param:
        print(f"[DEBUG] rawg_id provided directly, redirecting to /games/{rawg_id_param}/")
        return redirect('games:detail', game_id=str(rawg_id_param))
    
    # RAWG에서 제목으로 검색
    print(f"[DEBUG] Searching RAWG for: '{title}'")
    games = search_games(title, page_size=1)
    print(f"[DEBUG] RAWG search result: {len(games) if games else 0} games found")
    
    if games:
        rawg_id = games[0].get('id')
        print(f"[DEBUG] Found game! rawg_id={rawg_id}, redirecting to /games/{rawg_id}/")
        # 상세페이지로 리다이렉트 (game_detail에서 자동 생성됨)
        return redirect('games:detail', game_id=str(rawg_id))
    
    # 검색 결과 없음 - 메인으로 돌아감
    print(f"[DEBUG] No games found for '{title}', redirecting to main")
    from django.contrib import messages
    messages.warning(request, f'"{title}" 게임을 찾을 수 없습니다.')
    return redirect('users:main')

@login_required
def game_detail(request, game_id):
    """
    통합된 게임 상세 페이지 뷰
    
    1. DB에서 게임 조회 (Steam ID 또는 RAWG ID)
    2. DB에 없으면 RAWG API에서 가져와 자동 생성
    3. 모든 게임을 동일한 템플릿(detail.html)으로 렌더링
    """
    # Get RAWG API key from environment
    rawg_api_key = RAWG_API_KEY or os.getenv('RAWG_API_KEY', '')
    
    print(f"[DEBUG] game_detail called with game_id: {game_id} (type: {type(game_id).__name__})")
    
    numeric_id = extract_app_id(game_id)
    print(f"[DEBUG] Extracted numeric_id: {numeric_id}")
    
    game = None
    
    # 1. Steam 형식 ID (app123, bundle456 등)
    if is_steam_id(game_id):
        game = Game.objects.filter(steam_appid=numeric_id).first()
        print(f"[DEBUG] Steam ID search result: {game}")
    
    # 2. 순수 숫자 ID - Steam AppID로 먼저 검색
    if not game:
        game = Game.objects.filter(steam_appid=numeric_id).first()
        print(f"[DEBUG] Steam AppID search result: {game}")
    
    # 3. 여전히 없으면 RAWG ID로 검색
    if not game:
        game = Game.objects.filter(rawg_id=numeric_id).first()
    
    # 4. If still missing, check local DB ID (for Korean games etc)
    if not game:
        game = Game.objects.filter(id=numeric_id).first()
        print(f"[DEBUG] RAWG ID search result: {game}")
    
    # 4. DB에 없으면 RAWG API에서 가져와 자동 생성
    if not game:
        print(f"[DEBUG] Game not in DB, fetching from RAWG API...")
        rawg_data = fetch_rawg_game_details(numeric_id)
        print(f"[DEBUG] RAWG API result: {rawg_data is not None}")
        
        if rawg_data:
            # 게임 생성
            game = Game.objects.create(
                rawg_id=rawg_data.get('id'),
                title=rawg_data.get('name', f'Game {numeric_id}'),
                description=rawg_data.get('description_raw', ''),
                image_url=rawg_data.get('background_image', ''),
                background_image=rawg_data.get('background_image', ''),
                metacritic_score=rawg_data.get('metacritic'),
                genre=', '.join([g['name'] for g in rawg_data.get('genres', [])[:3]]) or '게임',
            )
            
            # 스크린샷 저장
            screenshots = fetch_rawg_screenshots(numeric_id)
            from .models import GameScreenshot
            for ss in screenshots[:8]:
                GameScreenshot.objects.get_or_create(
                    game=game,
                    image_url=ss.get('image', '')
                )
            
            print(f"✅ Auto-created game from RAWG: {game.title} (ID: {numeric_id})")
        else:
            # RAWG에서도 찾을 수 없음
            print(f"[DEBUG] ❌ Game not found anywhere, redirecting to main. game_id={game_id}")
            from django.contrib import messages
            messages.error(request, f'게임을 찾을 수 없습니다 (ID: {game_id})')
            return redirect('users:main')
    
    # 리뷰 POST 처리 (users.GameRating 사용)
    if request.method == 'POST':
        score = request.POST.get('score')
        comment = request.POST.get('comment', '')
        if score:
            GameRating.objects.update_or_create(
                user=request.user,
                game=game,
                defaults={'score': float(score), 'comment': comment}
            )
            return redirect('games:detail', game_id=game_id)
    
    # 유저 평가 데이터 (score=0 "안해봤어요"는 제외)
    user_ratings = GameRating.objects.filter(game=game).exclude(score=0).select_related('user').order_by('-updated_at')
    my_rating = GameRating.objects.filter(game=game, user=request.user).first()
    
    # Steam 크롤링 리뷰 (games.SteamReview - 한국어 리뷰)
    steam_reviews = game.steam_reviews.all()[:10]  # 상위 10개
    
    context = {
        'game': game,
        'user_ratings': user_ratings,
        'my_rating': my_rating,
        'steam_reviews': steam_reviews,
        'screenshots': game.screenshots.all(),
        'trailers': game.trailers.all(),
        'rawg_api_key': rawg_api_key,
    }
    return render(request, 'games/detail.html', context)

@login_required
def toggle_wishlist(request, game_id):
    app_id = extract_app_id(game_id)
    game = get_object_or_404(Game, steam_appid=app_id)
    user = request.user
    
    if user.wishlist.filter(pk=game.pk).exists():
        user.wishlist.remove(game)
        is_wishlisted = False
    else:
        user.wishlist.add(game)
        is_wishlisted = True
        
    return JsonResponse({'is_wishlisted': is_wishlisted})


# ============================================================================
# REST API Endpoints - Existing
# ============================================================================

@login_required
def api_wishlist_list(request):
    """Get user's wishlist as JSON"""
    wishlist_games = request.user.wishlist.all().values(
        'steam_appid', 'title', 'genre', 'image_url', 
        'description', 'metacritic_score'
    )
    return JsonResponse(list(wishlist_games), safe=False)

@login_required
def api_toggle_wishlist(request, game_id):
    """Toggle wishlist for a game via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    app_id = extract_app_id(game_id)
    game = get_object_or_404(Game, steam_appid=app_id)
    user = request.user
    
    if user.wishlist.filter(pk=game.pk).exists():
        user.wishlist.remove(game)
        is_wishlisted = False
    else:
        user.wishlist.add(game)
        is_wishlisted = True
    
    return JsonResponse({
        'success': True,
        'is_wishlisted': is_wishlisted,
        'game_id': game_id
    })

@login_required
def api_game_detail(request, game_id):
    """Get game details as JSON"""
    app_id = extract_app_id(game_id)
    game = get_object_or_404(Game, steam_appid=app_id)
    
    # Fetch RAWG data if not already fetched
    if not game.rawg_id or not game.background_image:
        update_game_with_rawg(game)
    
    screenshots = list(game.screenshots.all().values('image_url'))
    trailers = list(game.trailers.all().values('name', 'preview_url', 'data_480', 'data_max'))
    reviews = list(game.rating_set.all().values(
        'user__nickname', 'score', 'content', 'created_at', 'playtime_forever'
    ))
    
    game_data = {
        'steam_appid': game.steam_appid,
        'title': game.title,
        'genre': game.genre,
        'image_url': game.image_url,
        'rawg_id': game.rawg_id,
        'description': game.description,
        'background_image': game.background_image,
        'metacritic_score': game.metacritic_score,
        'screenshots': screenshots,
        'trailers': trailers,
        'reviews': reviews,
        'is_wishlisted': request.user.wishlist.filter(pk=game.pk).exists()
    }
    
    return JsonResponse(game_data)


# ============================================================================
# REST API Endpoints - RAWG Search & Classification
# ============================================================================

def api_search_games(request):
    """
    Search for games on RAWG API.
    
    Query params:
        q (required): Search query
        limit (optional): Number of results (default: 20)
    
    Example: /api/games/search/?q=witcher&limit=10
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'error': 'Query parameter "q" is required'}, status=400)
    
    limit = int(request.GET.get('limit', 20))
    
    results = search_games(query, page_size=limit)
    
    return JsonResponse({
        'query': query,
        'count': len(results),
        'results': results
    })


def api_get_genres(request):
    """
    Get list of all game genres from RAWG.
    
    Example: /api/games/genres/
    """
    genres = get_genres()
    
    return JsonResponse({
        'count': len(genres),
        'genres': genres
    })


def api_get_platforms(request):
    """
    Get list of all gaming platforms from RAWG.
    
    Example: /api/games/platforms/
    """
    platforms = get_platforms()
    
    return JsonResponse({
        'count': len(platforms),
        'platforms': platforms
    })


def api_games_by_genre(request, genre_slug):
    """
    Get games filtered by genre.
    
    Args:
        genre_slug: Genre slug (e.g., 'action', 'rpg', 'strategy')
    
    Query params:
        limit (optional): Number of results (default: 20)
    
    Example: /api/games/genre/action/?limit=10
    """
    limit = int(request.GET.get('limit', 20))
    
    results = get_games_by_genre(genre_slug, page_size=limit)
    
    return JsonResponse({
        'genre': genre_slug,
        'count': len(results),
        'games': results
    })


# ============================================================================
# REST API Endpoints - Popular & Trending Games
# ============================================================================

def api_popular_games(request):
    """
    Get most popular games (most added to libraries).
    Perfect for '요즘 뜨는 게임' section.
    Uses DB cache for faster loading.
    
    Query params:
        limit (optional): Number of results (default: 20)
        all_time (optional): If 'true', get all-time popular games without date filter
        refresh (optional): If 'true', force refresh from API
    
    Example: /api/games/popular/?limit=10&all_time=true
    """
    limit = int(request.GET.get('limit', 20))
    all_time = request.GET.get('all_time', 'false').lower() == 'true'
    force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
    
    # 캐시 카테고리 결정
    cache_category = 'popular'
    
    # 1. 캐시 먼저 확인 (force_refresh가 아닌 경우)
    if not force_refresh:
        cached_games = CachedGameList.get_cached_games(cache_category, max_age_hours=6)
        if cached_games:
            return JsonResponse({
                'count': min(len(cached_games), limit),
                'games': cached_games[:limit],
                'cached': True
            })
    
    # 2. RAWG API 호출
    results = get_popular_games(page_size=limit, all_time=all_time)
    
    # 3. 캐시에 저장 (limit 이상 가져와서 저장)
    if results:
        CachedGameList.set_cached_games(cache_category, results)
    
    return JsonResponse({
        'count': len(results),
        'games': results,
        'cached': False
    })


def api_top_rated_games(request):
    """
    Get highest rated games.
    Uses DB cache for faster loading.
    
    Query params:
        limit (optional): Number of results (default: 20)
        refresh (optional): If 'true', force refresh from API
    
    Example: /api/games/top-rated/?limit=10
    """
    limit = int(request.GET.get('limit', 20))
    force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
    
    cache_category = 'top_rated'
    
    if not force_refresh:
        cached_games = CachedGameList.get_cached_games(cache_category, max_age_hours=6)
        if cached_games:
            return JsonResponse({
                'count': min(len(cached_games), limit),
                'games': cached_games[:limit],
                'cached': True
            })
    
    results = get_top_rated_games(page_size=limit)
    
    if results:
        CachedGameList.set_cached_games(cache_category, results)
    
    return JsonResponse({
        'count': len(results),
        'games': results,
        'cached': False
    })


def api_trending_games(request):
    """
    Get games with highest metacritic scores.
    Uses DB cache for faster loading.
    
    Query params:
        limit (optional): Number of results (default: 20)
        refresh (optional): If 'true', force refresh from API
    
    Example: /api/games/trending/?limit=10
    """
    limit = int(request.GET.get('limit', 20))
    force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
    
    cache_category = 'trending'
    
    if not force_refresh:
        cached_games = CachedGameList.get_cached_games(cache_category, max_age_hours=6)
        if cached_games:
            return JsonResponse({
                'count': min(len(cached_games), limit),
                'games': cached_games[:limit],
                'cached': True
            })
    
    results = get_trending_games(page_size=limit)
    
    if results:
        CachedGameList.set_cached_games(cache_category, results)
    
    return JsonResponse({
        'count': len(results),
        'games': results,
        'cached': False
    })


def api_new_releases(request):
    """
    Get recently released games.
    Uses DB cache for faster loading.
    
    Query params:
        limit (optional): Number of results (default: 20)
        refresh (optional): If 'true', force refresh from API
    
    Example: /api/games/new-releases/?limit=10
    """
    limit = int(request.GET.get('limit', 20))
    force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
    
    cache_category = 'new_releases'
    
    if not force_refresh:
        cached_games = CachedGameList.get_cached_games(cache_category, max_age_hours=6)
        if cached_games:
            return JsonResponse({
                'count': min(len(cached_games), limit),
                'games': cached_games[:limit],
                'cached': True
            })
    
    results = get_new_releases(page_size=limit)
    
    if results:
        CachedGameList.set_cached_games(cache_category, results)
    
    return JsonResponse({
        'count': len(results),
        'games': results,
        'cached': False
    })


def api_upcoming_games(request):
    """
    Get upcoming games (to be released).
    
    Query params:
        limit (optional): Number of results (default: 20)
    
    Example: /api/games/upcoming/?limit=10
    """
    limit = int(request.GET.get('limit', 20))
    results = get_upcoming_games(page_size=limit)
    
    return JsonResponse({
        'count': len(results),
        'games': results
    })


def api_games_by_ordering(request):
    """
    Get games sorted by custom ordering.
    
    Query params:
        ordering (required): Sorting option
            Available: -added, -rating, -metacritic, -released, name, etc.
        limit (optional): Number of results (default: 20)
    
    Example: /api/games/ordered/?ordering=-rating&limit=10
    """
    ordering = request.GET.get('ordering', '-added')
    limit = int(request.GET.get('limit', 20))
    
    results = get_games_by_ordering(ordering=ordering, page_size=limit)
    
    return JsonResponse({
        'ordering': ordering,
        'count': len(results),
        'games': results
    })


# ============================================================================
# REST API Endpoints - Reviews for RAWG Games
# ============================================================================

import json
from django.views.decorators.http import require_http_methods

@login_required
@require_http_methods(["GET"])
def api_reviews_by_rawg_id(request, rawg_id):
    """
    RAWG ID로 게임 리뷰 목록 가져오기
    
    Returns:
        - reviews: 리뷰 목록
        - my_review: 현재 사용자의 리뷰 (있을 경우)
        - game_exists: DB에 게임이 있는지 여부
    """
    try:
        # 중복 rawg_id가 있을 수 있으므로 filter 사용
        game = Game.objects.filter(rawg_id=rawg_id).first()
        if not game:
            raise Game.DoesNotExist
        # users.GameRating 사용 (실제 데이터)
        ratings = GameRating.objects.filter(game=game).select_related('user').order_by('-updated_at')
        my_rating = ratings.filter(user=request.user).first()
        
        reviews_data = [{
            'id': r.id,
            'user': r.user.nickname or r.user.username,
            'score': r.score,
            'created_at': r.updated_at.strftime('%Y.%m.%d'),
        } for r in ratings]
        
        return JsonResponse({
            'game_exists': True,
            'game_id': game.id,
            'reviews': reviews_data,
            'review_count': len(reviews_data),
            'my_review': {
                'score': my_rating.score,
            } if my_rating else None
        })
    except Game.DoesNotExist:
        return JsonResponse({
            'game_exists': False,
            'reviews': [],
            'review_count': 0,
            'my_review': None
        })


@login_required
@require_http_methods(["POST"])
def api_toggle_wishlist_by_rawg_id(request, rawg_id):
    """
    RAWG ID로 게임 찜하기 토글 (게임이 DB에 없으면 자동 생성)
    
    Body:
        - game_title: 게임 제목 (게임 생성 시 필요)
        - game_image: 게임 이미지 URL (optional)
    """
    try:
        data = json.loads(request.body)
        game_title = data.get('game_title', f'Game {rawg_id}')
        game_image = data.get('game_image', '')
        
        # 게임 찾기 (중복 rawg_id가 있을 수 있으므로 filter 사용)
        game = Game.objects.filter(rawg_id=rawg_id).first()
        created = False
        
        if not game:
            # 게임이 없으면 새로 생성
            game = Game.objects.create(
                rawg_id=rawg_id,
                title=game_title,
                image_url=game_image,
                background_image=game_image,
                genre='게임',
            )
            created = True
            print(f"Created new game for wishlist from RAWG: {game_title} (rawg_id: {rawg_id})")
        
        # 찜하기 토글
        user = request.user
        if user.wishlist.filter(pk=game.pk).exists():
            user.wishlist.remove(game)
            is_wishlisted = False
        else:
            user.wishlist.add(game)
            is_wishlisted = True
        
        return JsonResponse({
            'success': True,
            'is_wishlisted': is_wishlisted,
            'game_id': game.rawg_id,
            'steam_appid': game.steam_appid,
            'game_created': created,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        import traceback
        print(f"Wishlist toggle error: {e}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_wishlist_status_by_rawg_id(request, rawg_id):
    """
    RAWG ID로 게임 찜 상태 확인 (로그인 여부 확인 후)
    
    Returns:
        - is_wishlisted: True/False
    """
    # 로그인하지 않은 경우
    if not request.user.is_authenticated:
        return JsonResponse({
            'is_wishlisted': False,
            'authenticated': False
        })
    
    try:
        # 중복 rawg_id가 있을 수 있으므로 filter 사용
        game = Game.objects.filter(rawg_id=rawg_id).first()
        if not game:
            return JsonResponse({
                'is_wishlisted': False,
                'authenticated': True,
                'game_exists': False
            })
        is_wishlisted = request.user.wishlist.filter(pk=game.pk).exists()
        
        return JsonResponse({
            'is_wishlisted': is_wishlisted,
            'authenticated': True,
            'game_id': game.rawg_id
        })
    except Game.DoesNotExist:
        return JsonResponse({
            'is_wishlisted': False,
            'authenticated': True,
            'game_exists': False
        })


@login_required
@require_http_methods(["POST"])
def api_submit_review_by_rawg_id(request, rawg_id):
    """
    RAWG ID로 게임 리뷰 작성 (게임이 DB에 없으면 자동 생성)
    
    Body:
        - score: 평점 (1~5)
        - content: 리뷰 내용 (optional)
        - game_title: 게임 제목 (게임 생성 시 필요)
        - game_image: 게임 이미지 URL (optional)
    """
    try:
        data = json.loads(request.body)
        score = float(data.get('score', 0))
        content = data.get('content', '')
        game_title = data.get('game_title', f'Game {rawg_id}')
        game_image = data.get('game_image', '')
        
        if score < 1 or score > 5:
            return JsonResponse({'error': '평점은 1~5 사이여야 합니다.'}, status=400)
        
        # 게임 찾기 또는 생성
        game, created = Game.objects.get_or_create(
            rawg_id=rawg_id,
            defaults={
                'title': game_title,
                'image_url': game_image,
                'background_image': game_image,
                'genre': '게임',
            }
        )
        
        if created:
            print(f"Created new game from RAWG: {game_title} (rawg_id: {rawg_id})")
        
        # 평가 저장/업데이트 (users.GameRating 사용)
        rating, rating_created = GameRating.objects.update_or_create(
            user=request.user,
            game=game,
            defaults={
                'score': score,
            }
        )
        
        return JsonResponse({
            'success': True,
            'review_id': rating.id,
            'created': rating_created,
            'game_id': game.id,
            'game_created': created,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        import traceback
        print(f"Review error: {e}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_translate_game(request):
    """
    Translate game description to Korean and save to DB.
    
    Body:
        - game_pk: Game DB ID (optional)
        - rawg_id: RAWG ID (optional)
        - text: Text to translate (only used if game not found yet)
        - game_title: Title for creating new game (optional)
    """
    import os
    import json
    import requests
    from dotenv import load_dotenv
    from .utils import translate_text_gemini
    load_dotenv()
    
    api_key = os.getenv('GMS_API_KEY')
    if not api_key:
        return JsonResponse({'error': 'API 키가 설정되지 않았습니다.', 'success': False}, status=500)
        
    try:
        data = json.loads(request.body)
        game_pk = data.get('game_pk')
        rawg_id = data.get('rawg_id')
        text_to_translate = data.get('text', '').strip()
        
        game = None
        
        # 1. Find Game
        if game_pk:
            game = get_object_or_404(Game, pk=game_pk)
        elif rawg_id:
            game = Game.objects.filter(rawg_id=rawg_id).first()
            
        # 2. If Game found, check existing translation
        if game:
            if game.description_kr:
                return JsonResponse({
                    'success': True,
                    'translated': game.description_kr,
                    'cached': True
                })
            
            # Use game description if text not provided/empty
            if not text_to_translate:
                text_to_translate = game.description
                
            # If description is empty also, try to fetch from RAWG (if rawg_id)
            if not text_to_translate and game.rawg_id:
                details = fetch_rawg_game_details(game.rawg_id)
                if details:
                    text_to_translate = details.get('description_raw', '') or details.get('description', '')
                    game.description = text_to_translate
                    game.save(update_fields=['description'])

        # 3. Use text provided if game not found (for new games)
        if not game and rawg_id:
             # Create game shell to store translation
            game_title = data.get('game_title', f'Game {rawg_id}')
            game = Game.objects.create(
                rawg_id=rawg_id,
                title=game_title,
                genre='Unknown'
            )
            # Try to fetch full details
            details = fetch_rawg_game_details(rawg_id)
            if details:
                game.title = details.get('name', game_title)
                game.image_url = details.get('background_image', '')
                game.background_image = details.get('background_image', '')
                game.description = details.get('description_raw', '') or details.get('description', '')
                text_to_translate = game.description
                
                # Genres
                if details.get('genres'):
                     game.genre = ', '.join([g['name'] for g in details['genres'][:3]])
                
                game.save()
            
        if not text_to_translate:
             return JsonResponse({'error': '번역할 텍스트가 없습니다.', 'success': False}, status=400)

        # 4. Call Gemini API
        translated_text = translate_text_gemini(text_to_translate)
        
        if translated_text:
            # Save to DB if game exists
            if game:
                game.description_kr = translated_text
                # Also save original if it was empty
                if not game.description:
                    game.description = text_to_translate
                game.save()
                
            return JsonResponse({
                'success': True,
                'translated': translated_text,
                'cached': False
            })
                
        return JsonResponse({'error': 'AI 번역 실패', 'success': False}, status=500)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': str(e), 'success': False}, status=500)


def api_autocomplete_games(request):
    """
    게임 자동완성 API - DB에서 제목으로 검색
    
    Query params:
        q (required): 검색 쿼리
        limit (optional): 결과 개수 (default: 10)
    
    Returns:
        - games: 일치하는 게임 목록 (id, title, image_url, genre)
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 1:
        return JsonResponse({'games': []})
    
    limit = min(int(request.GET.get('limit', 10)), 20)
    
    # DB에서 제목으로 검색 (대소문자 무시)
    from django.db.models import Q
    games = Game.objects.filter(
        Q(title__icontains=query)
    ).values('id', 'rawg_id', 'title', 'image_url', 'genre')[:limit]
    
    result = [{
        'id': g['rawg_id'] or g['id'],
        'title': g['title'],
        'image_url': g['image_url'],
        'genre': g['genre']
    } for g in games]
    
    return JsonResponse({'games': result})
