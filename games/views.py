from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from .models import Game, Rating, CachedGameList
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
    Render game detail page for searching by title.
    Used by sale tab where Steam AppID != RAWG ID.
    
    The client-side JavaScript will read the 'title' query param
    and search RAWG API directly for better performance.
    
    Query params:
        title (required): Game title to search
        steam_appid (optional): Steam AppID for price comparison links
    """
    title = request.GET.get('title', '').strip()
    steam_appid = request.GET.get('steam_appid', '')
    
    if not title:
        return redirect('users:main')
    
    rawg_api_key = RAWG_API_KEY or os.getenv('RAWG_API_KEY', '')
    
    # Simply render detail.html - client-side JavaScript will handle the RAWG search
    context = {
        'game': None,
        'is_rawg_only': True,
        'rawg_api_key': rawg_api_key,
        'search_title': title,
        'steam_appid': steam_appid,
    }
    return render(request, 'games/detail.html', context)

@login_required
def game_detail(request, game_id):
    """
    Game detail view - optimized for lazy loading.
    - DB games (Steam): Server-side rendering with full data
    - RAWG games: Client-side rendering with JavaScript
    """
    # Get RAWG API key from environment
    rawg_api_key = RAWG_API_KEY or os.getenv('RAWG_API_KEY', '')
    
    # 1. Steam 형식의 ID인 경우 (app123, bundle456 등) - DB에서 가져오기
    if is_steam_id(game_id):
        app_id = extract_app_id(game_id)
        try:
            game = Game.objects.get(steam_appid=app_id)
        except Game.DoesNotExist:
            # DB에 없으면 RAWG 전용으로 처리
            context = {
                'game': None,
                'is_rawg_only': True,
                'rawg_api_key': rawg_api_key,
            }
            return render(request, 'games/detail.html', context)
        
        # DB 게임 - 서버사이드 렌더링 (기존 detail_db.html 사용)
        if request.method == 'POST':
            score = request.POST.get('score')
            content = request.POST.get('content')
            if score:
                Rating.objects.update_or_create(
                    user=request.user,
                    game=game,
                    defaults={'score': float(score), 'content': content}
                )
                return redirect('games:detail', game_id=game_id)
        
        reviews = Rating.objects.filter(game=game).select_related('user').order_by('-updated_at')
        my_review = reviews.filter(user=request.user).first()
        
        context = {
            'game': game,
            'reviews': reviews,
            'my_review': my_review,
            'screenshots': game.screenshots.all(),
            'trailers': game.trailers.all(),
            'is_rawg_only': False,
            'rawg_api_key': rawg_api_key,
        }
        return render(request, 'games/detail_db.html', context)
    
    # 2. 순수 숫자 ID인 경우 - RAWG ID로 간주하고 클라이언트에서 로딩
    numeric_id = extract_app_id(game_id)
    
    # 먼저 DB에서 검색
    try:
        game = Game.objects.get(steam_appid=numeric_id)
        # DB 게임 찾음 - 서버사이드 렌더링
        if request.method == 'POST':
            score = request.POST.get('score')
            content = request.POST.get('content')
            if score:
                Rating.objects.update_or_create(
                    user=request.user,
                    game=game,
                    defaults={'score': float(score), 'content': content}
                )
                return redirect('games:detail', game_id=game_id)
        
        reviews = Rating.objects.filter(game=game).select_related('user').order_by('-updated_at')
        my_review = reviews.filter(user=request.user).first()
        
        context = {
            'game': game,
            'reviews': reviews,
            'my_review': my_review,
            'screenshots': game.screenshots.all(),
            'trailers': game.trailers.all(),
            'is_rawg_only': False,
            'rawg_api_key': rawg_api_key,
        }
        return render(request, 'games/detail_db.html', context)
    except Game.DoesNotExist:
        pass
    
    try:
        game = Game.objects.get(rawg_id=numeric_id)
        # DB 게임 찾음 - 서버사이드 렌더링
        context = {
            'game': game,
            'reviews': Rating.objects.filter(game=game).select_related('user').order_by('-updated_at'),
            'my_review': Rating.objects.filter(game=game, user=request.user).first(),
            'screenshots': game.screenshots.all(),
            'trailers': game.trailers.all(),
            'is_rawg_only': False,
            'rawg_api_key': rawg_api_key,
        }
        return render(request, 'games/detail_db.html', context)
    except Game.DoesNotExist:
        pass
    
    # DB에 없으면 RAWG 전용 - 클라이언트사이드 렌더링 (빠른 로딩)
    context = {
        'game': None,
        'is_rawg_only': True,
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
        game = Game.objects.get(rawg_id=rawg_id)
        reviews = Rating.objects.filter(game=game).select_related('user').order_by('-updated_at')
        my_review = reviews.filter(user=request.user).first()
        
        reviews_data = [{
            'id': r.id,
            'user': r.user.nickname,
            'score': r.score,
            'content': r.content,
            'created_at': r.updated_at.strftime('%Y.%m.%d'),
        } for r in reviews]
        
        return JsonResponse({
            'game_exists': True,
            'game_id': game.id,
            'reviews': reviews_data,
            'review_count': len(reviews_data),
            'my_review': {
                'score': my_review.score,
                'content': my_review.content,
            } if my_review else None
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
        
        # 리뷰 저장/업데이트
        rating, rating_created = Rating.objects.update_or_create(
            user=request.user,
            game=game,
            defaults={
                'score': score,
                'content': content
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

