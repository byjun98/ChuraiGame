"""
온보딩 시스템 및 Item-Based Collaborative Filtering
왓챠 스타일의 콜드 스타트 해결

알고리즘 전략:
1. 온보딩 단계 (Rule-Based): 인기 게임(리뷰 많은 순) 표시 - JSON에서 로드
2. 평가 진행 중 (Content-Based): 평가한 게임과 유사한 게임 추천
3. 데이터 축적 후 (Item-Based CF): 게임 간 유사도 기반 추천
"""

import json
import os
import pandas as pd
import numpy as np
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.conf import settings
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

# JSON에서 온보딩 게임 로드 (캐시)
_onboarding_games_cache = None
_korean_games_cache = None


def clear_korean_games_cache():
    """한국 게임 캐시 무효화 (데이터 업데이트 후 호출)"""
    global _korean_games_cache
    _korean_games_cache = None
    logger.info("Korean games cache cleared")


def load_korean_games_from_db():
    """
    DB에서 한국 유명 게임 목록 로드 (온보딩 '아니요' 선택 시 사용)
    korean 태그가 있거나 한국어 제목이 포함된 게임
    
    개선사항:
    - 이미지가 있는 게임만 필터링
    - 더 많은 제목 패턴 매칭
    - RAWG 데이터가 있는 게임 우선
    """
    global _korean_games_cache
    
    if _korean_games_cache is not None:
        return _korean_games_cache
    
    from games.models import Game
    
    try:
        # 1. korean 태그가 있는 게임
        korean_tagged = Game.objects.filter(
            tags__slug='korean'
        ).distinct()
        
        # 2. 한글/영문 제목 패턴 매칭 (더 포괄적으로)
        korean_titles_pattern = [
            # 한국 온라인게임
            '메이플', '던전앤파이터', '던파', '리니지', '마비노기', '서든', '카스',
            '카트라이더', '테일즈런너', '크레이지', '바람의나라', '뮤 온라인', '뮤',
            '블레이드앤소울', '검은사막', '로스트아크', '엘소드', '그랜드체이스',
            '아이온', '마영전', '블루아카이브', '쿠키런', '니케', '명일방주',
            # 글로벌 인기 게임 (한국에서 유행)
            'MapleStory', 'Lost Ark', 'Black Desert', 'PUBG', 'Overwatch',
            'Valorant', 'League of Legends', 'StarCraft', 'Diablo', 'FIFA',
            'Counter-Strike', 'Dungeon Fighter', 'Mabinogi', 'Lineage', 'Vindictus',
            # 닌텐도/콘솔 게임
            'Mario', 'Zelda', 'Pokemon', 'Animal Crossing', '동물의 숲', '포켓몬',
            'Splatoon', 'Kirby', 'Fire Emblem', 'Xenoblade', 'Metroid',
            # 모바일 게임
            'Genshin', 'Honkai', 'Arknights', 'Fate/Grand', 'Blue Archive',
            'Cookie Run', 'Clash of Clans', 'Clash Royale', 'Brawl Stars',
            'Among Us', 'Fall Guys', 'Roblox', 'Marvel Snap',
            # 추가 한국 게임
            '스페셜포스', '배틀그라운드', '발로란트', '오버워치', '리그 오브',
        ]
        
        from django.db.models import Q
        title_filter = Q()
        for pattern in korean_titles_pattern:
            title_filter |= Q(title__icontains=pattern)
        
        title_matched = Game.objects.filter(title_filter).distinct()
        
        # 3. 두 쿼리 결과 합치기 (Union)
        all_korean_games = korean_tagged | title_matched
        
        # 4. 이미지가 있는 게임만 필터링 + RAWG 데이터 있는 것 우선
        all_korean_games = all_korean_games.filter(
            Q(image_url__isnull=False, image_url__gt='') |
            Q(background_image__isnull=False, background_image__gt='') |
            Q(steam_appid__isnull=False)
        ).distinct().order_by('-rawg_id', '-metacritic_score')
        
        formatted_games = []
        seen_titles = set()  # 중복 제거용
        
        for game in all_korean_games:
            # 제목 중복 체크 (한글/영문 중복 방지)
            title_key = game.title.split(' (')[0].lower().strip()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            
            # 이미지 URL 결정 (우선순위: background_image > image_url > Steam CDN)
            image = game.background_image or game.image_url or ''
            if not image and game.steam_appid:
                # Steam CDN 폴백
                image = f'https://cdn.cloudflare.steamstatic.com/steam/apps/{game.steam_appid}/header.jpg'
            
            # 이미지가 없으면 스킵
            if not image:
                continue
            
            formatted_games.append({
                'title': game.title,
                'rawg_id': game.rawg_id or game.id,  # rawg_id 없으면 DB id 사용
                'steam_app_id': game.steam_appid,
                'image': image,
                'genre': game.genre,
                'description': game.description[:100] if game.description else '',
                'metacritic': game.metacritic_score,
            })
        
        _korean_games_cache = formatted_games
        logger.info(f"Loaded {len(formatted_games)} Korean games from DB for onboarding")
        return _korean_games_cache
        
    except Exception as e:
        logger.error(f"Error loading Korean games from DB: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def load_onboarding_games_from_json():
    """
    JSON 데이터셋에서 리뷰가 많은 인기 게임을 로드하여 온보딩용 데이터로 변환
    Steam CDN 썸네일 사용 (빠른 로딩)
    """
    global _onboarding_games_cache
    
    if _onboarding_games_cache is not None:
        return _onboarding_games_cache
    
    json_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 1. Steam 평점 75% 이상, 리뷰 500개 이상인 게임만 필터링 (더 많은 게임 포함)
        quality_games = [
            g for g in data 
            if g.get('steam_rating', 0) >= 75 
            and g.get('review_count', 0) >= 500
        ]
        
        # 2. 리뷰 수(review_count) 기준으로 내림차순 정렬 (인기 게임 추출)
        sorted_games = sorted(
            quality_games, 
            key=lambda x: x.get('review_count', 0), 
            reverse=True
        )
        
        # 3. 상위 500개 게임 추출 (이미 평가한 게임 제외해도 충분하도록)
        top_games = sorted_games[:500]
        
        # 4. 온보딩 형식에 맞게 데이터 가공 (Steam CDN 이미지 사용!)
        formatted_games = []
        for game in top_games:
            # 실제 RAWG ID 사용 (없으면 steam_app_id를 폴백으로)
            rawg_id = game.get('rawg_id') or int(game['steam_app_id'])
            
            formatted_games.append({
                'title': game['title'],
                'rawg_id': rawg_id,  # 실제 RAWG ID 사용
                'rawg_slug': game.get('rawg_slug', ''),  # RAWG 슬러그 (URL용)
                'steam_app_id': game.get('steam_app_id'),
                'image': game['thumbnail'],  # Steam CDN 이미지 (빠름!)
                'steam_rating': game.get('steam_rating', 0),
                'review_count': game.get('review_count', 0),
            })
        
        # 5. 캐시 저장
        _onboarding_games_cache = {
            'popular': formatted_games
        }
        
        logger.info(f"Loaded {len(formatted_games)} games from JSON for onboarding")
        return _onboarding_games_cache
        
    except Exception as e:
        logger.error(f"Error loading onboarding games from JSON: {e}")
        return {'popular': []}


# 온보딩 단계별 설정 (인기 게임 단일 단계로 간소화)
ONBOARDING_STEPS = [
    {'name': '인기 게임', 'genre': 'popular', 'description': '평가가 많은 인기 게임들이에요. 아는 게임을 평가해주세요!'},
]


def get_onboarding_games(step=0, exclude_rated=None, page=1, per_page=8, korean_mode=False):
    """
    온보딩 단계별 게임 목록 반환 (페이지네이션 지원)
    
    Args:
        step: 현재 단계 (0만 사용)
        exclude_rated: 이미 평가한 게임 ID 리스트
        page: 현재 페이지 (1부터 시작)
        per_page: 페이지당 게임 수 (기본값: 8 - 2행x4열)
        korean_mode: True면 한국 유명 게임 목록 사용 (Steam 미경험자용)
    
    Returns:
        dict: {games: [...], step_info: {...}, pagination: {...}}
    """
    # 한국 게임 모드면 DB에서 로드
    if korean_mode:
        games = load_korean_games_from_db()
        step_info = {
            'name': '한국 인기 게임',
            'genre': 'korean',
            'description': '국내에서 유행했던 게임들이에요. 플레이해본 적 있는 게임을 평가해주세요!'
        }
    else:
        # JSON에서 게임 로드 (기존 Steam 게임)
        onboarding_games = load_onboarding_games_from_json()
        
        if step >= len(ONBOARDING_STEPS):
            return {'games': [], 'step_info': None, 'is_complete': True}
        
        step_info = ONBOARDING_STEPS[step]
        genre = step_info['genre']
        games = onboarding_games.get(genre, [])
    
    # 이미 평가한 게임 제외 (set으로 변환하여 O(1) 검색)
    if exclude_rated:
        exclude_set = set(exclude_rated)
        games = [g for g in games if g.get('rawg_id') not in exclude_set]
    
    # 페이지네이션 계산
    total_games = len(games)
    total_pages = (total_games + per_page - 1) // per_page  # 올림 나눗셈
    
    # 페이지 범위 제한
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    # 현재 페이지의 게임만 추출
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_games = games[start_idx:end_idx]
    
    return {
        'games': paginated_games,
        'step_info': step_info,
        'current_step': step,
        'total_steps': len(ONBOARDING_STEPS),
        'is_complete': False,
        'korean_mode': korean_mode,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'per_page': per_page,
            'total_games': total_games,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
    }



def calculate_game_similarity_batch(min_ratings=1, top_k=50, min_similarity=0.1):
    """
    배치 작업: 게임 간 유사도 계산
    
    매일 새벽에 실행하여 GameSimilarity 테이블 갱신
    - Item-Based Collaborative Filtering 사용
    - 희소 행렬로 메모리 효율화
    - transaction.atomic()으로 안전한 데이터 갱신
    
    ⚠️ 새 스키마 규칙:
    - game_a_id < game_b_id 정규화 (저장 공간 50% 절약)
    - similarity_rank 계산 (Top-K 쿼리 최적화)
    - 평점 정규화: -1→-1.0, 3.5→0.7, 5→1.0
    
    Args:
        min_ratings: 최소 평가 수 (이보다 적은 평가를 받은 게임은 제외)
        top_k: 각 게임마다 저장할 유사 게임 수
        min_similarity: 저장할 최소 유사도
    
    Note:
        이 함수 대신 Management Command 사용을 권장합니다:
        python manage.py calculate_game_similarity --min-ratings 3 --top-k 50
    """
    from django.db import transaction
    from .models import GameRating, GameSimilarity
    from games.models import Game
    
    # 평점 정규화 (비선형 → 선형)
    SCORE_NORMALIZATION = {-1: -1.0, 0: 0.0, 3.5: 0.7, 5: 1.0}
    
    logger.info("Starting game similarity batch calculation...")
    
    # 1. 모든 평가 데이터 가져오기 (필요한 컬럼만)
    ratings = list(GameRating.objects.filter(score__gt=0).values('user_id', 'game_id', 'score'))
    
    if len(ratings) < 10:
        logger.warning("Not enough rating data for similarity calculation")
        return {'success': False, 'message': 'Not enough rating data'}
    
    df = pd.DataFrame(ratings)
    
    # 평점 정규화 적용
    df['normalized_score'] = df['score'].apply(lambda x: SCORE_NORMALIZATION.get(x, x / 5.0))
    
    # 게임별 평가 수 계산 및 필터링
    game_rating_counts = df.groupby('game_id').size()
    valid_games = game_rating_counts[game_rating_counts >= min_ratings].index.tolist()
    df = df[df['game_id'].isin(valid_games)]
    
    if len(df) < 10:
        logger.warning("Not enough games with sufficient ratings")
        return {'success': False, 'message': 'Not enough games with sufficient ratings'}
    
    # 2. 희소 행렬 생성 (게임 x 유저)
    user_cat = df['user_id'].astype('category')
    game_cat = df['game_id'].astype('category')
    
    user_codes = user_cat.cat.codes.values
    game_codes = game_cat.cat.codes.values
    scores = df['normalized_score'].values  # 정규화된 점수 사용
    
    # 희소 행렬 생성 (행: 게임, 열: 유저, 값: 정규화된 점수)
    sparse_matrix = csr_matrix(
        (scores, (game_codes, user_codes)),
        shape=(len(game_cat.cat.categories), len(user_cat.cat.categories))
    )
    
    logger.info(f"Created sparse matrix: {sparse_matrix.shape[0]} games x {sparse_matrix.shape[1]} users")
    
    # 3. 게임 간 코사인 유사도 계산
    similarity_matrix = cosine_similarity(sparse_matrix)
    
    # 4. 정규화 및 랭크 계산 (game_a_id < game_b_id)
    game_ids = game_cat.cat.categories.tolist()
    pair_data = {}  # (game_a_id, game_b_id) -> {'score': float, 'rank': int}
    
    for i, game_x_id in enumerate(game_ids):
        sim_scores = similarity_matrix[i]
        sorted_indices = np.argsort(sim_scores)[::-1]
        
        rank = 0
        for j in sorted_indices:
            if i == j:
                continue
            
            score = sim_scores[j]
            if score < min_similarity:
                break
            
            rank += 1
            if rank > top_k:
                break
            
            game_y_id = game_ids[j]
            
            # 정규화: 항상 작은 ID를 game_a로
            game_a_id = min(game_x_id, game_y_id)
            game_b_id = max(game_x_id, game_y_id)
            pair_key = (game_a_id, game_b_id)
            
            if pair_key not in pair_data:
                pair_data[pair_key] = {'score': score, 'rank': rank}
            else:
                pair_data[pair_key]['rank'] = min(pair_data[pair_key]['rank'], rank)
    
    # 5. 트랜잭션으로 안전하게 저장
    try:
        with transaction.atomic():
            # 기존 데이터 삭제
            deleted_count, _ = GameSimilarity.objects.all().delete()
            
            # GameSimilarity 객체 생성 및 벌크 저장
            similarities_to_create = [
                GameSimilarity(
                    game_a_id=pair[0],
                    game_b_id=pair[1],
                    similarity_score=data['score'],
                    similarity_rank=data['rank']
                ) for pair, data in pair_data.items()
            ]
            GameSimilarity.objects.bulk_create(similarities_to_create, batch_size=1000)
        
        logger.info(f"Created {len(similarities_to_create)} similarity records (deleted {deleted_count} old)")
        return {
            'success': True, 
            'created': len(similarities_to_create),
            'deleted': deleted_count,
            'normalized': True
        }
    except Exception as e:
        logger.error(f"Batch calculation failed: {e}")
        return {'success': False, 'message': str(e)}



def get_recommendations_for_user(user, limit=50):
    """
    사용자에게 게임 추천
    
    전략:
    1. 평가 데이터가 없으면 -> JSON 인기 게임 반환 (빠름!)
    2. 평가 데이터가 있으면 -> DB 기반 추천 시도
    3. DB 추천 결과가 부족하면 -> JSON 인기 게임으로 보충
    
    Args:
        user: User 객체
        limit: 반환할 추천 게임 수
    
    Returns:
        dict: {needs_onboarding, recommendations, method}
    """
    from .models import GameRating, GameSimilarity
    from games.models import Game
    
    def format_json_games(json_games, base_score=80, rated_ids=None):
        """JSON 게임 데이터를 프론트엔드 형식으로 변환"""
        rated_ids = rated_ids or []
        result = []
        for i, game in enumerate(json_games):
            # 실제 RAWG ID 사용 (없으면 steam_app_id를 폴백으로)
            rawg_id = game.get('rawg_id') or int(game.get('steam_app_id', 0) or 0)
            steam_id = int(game.get('steam_app_id', 0) or 0)
            
            # 이미 평가한 게임 제외 (rawg_id로 확인)
            if rawg_id in rated_ids:
                continue
            
            steam_rating = game.get('steam_rating', 0)
            review_count = game.get('review_count', 0)
            
            # 추천 점수 = 기본점수 + Steam평점/5 - 순서 패널티
            score = base_score + (steam_rating / 5) - (len(result) * 0.3)
            score = max(50, min(100, score))
            
            result.append({
                'id': None,  # DB ID 없음
                'rawg_id': rawg_id,  # 실제 RAWG ID 사용
                'rawg_slug': game.get('rawg_slug', ''),  # RAWG 슬러그 (URL용)
                'steam_app_id': game.get('steam_app_id'),
                'title': game['title'],
                'image_url': game.get('thumbnail', ''),  # Steam CDN (빠름!)
                'rating': round(steam_rating / 20, 1) if steam_rating else 0,
                'metacritic': game.get('metacritic_score'),
                'genres': [],  # JSON에 장르 없음
                'recommendation_score': round(score, 1),
                'is_on_sale': game.get('is_on_sale', False),
                'discount_rate': round(game.get('discount_rate', 0) * 100),
                'current_price': game.get('current_price'),
                'original_price': game.get('original_price'),
                'review_count': review_count,
            })
            
            if len(result) >= limit:
                break
                
        return result
    
    def format_db_games(games_queryset, base_score=80):
        """DB 게임 데이터를 프론트엔드 형식으로 변환"""
        result = []
        for i, game in enumerate(games_queryset):
            metacritic = float(game.metacritic_score) if game.metacritic_score else 0
            score = base_score + (metacritic / 5) - (i * 0.5)
            score = max(50, min(100, score))
            image = getattr(game, 'image_url', '') or getattr(game, 'background_image', '') or ''
            
            result.append({
                'id': game.id,
                'rawg_id': game.rawg_id,
                'title': game.title,
                'image_url': image,
                'rating': round(metacritic / 20, 1) if metacritic else 0,
                'metacritic': int(metacritic) if metacritic else None,
                'genres': game.genre.split(',')[:3] if game.genre else [],
                'recommendation_score': round(score, 1),
                'is_on_sale': False,
            })
        return result
    
    # JSON 인기 게임 로드 (폴백용)
    json_data = load_onboarding_games_from_json()
    popular_from_json = json_data.get('popular', [])
    
    # 사용자의 평가 데이터 가져오기
    user_ratings = GameRating.objects.filter(user=user, score__gt=0)
    rated_game_ids = list(user_ratings.values_list('game_id', flat=True))
    rated_steam_ids = list(user_ratings.values_list('game__rawg_id', flat=True))
    
    # 1. 평가 데이터가 없으면 -> JSON 인기 게임 반환 (빠름!)
    if len(rated_game_ids) == 0:
        return {
            'needs_onboarding': False,  # 온보딩 모달 대신 바로 추천 보여줌
            'recommendations': format_json_games(popular_from_json, 80, []),
            'method': 'popular_json',
            'message': '인기 게임을 추천해드려요! 게임을 평가하면 맞춤 추천이 더 정확해져요.'
        }
    
    # 2. 사용자가 좋아한 게임 (따봉 이상)
    liked_games = user_ratings.filter(score__gte=3.5).values_list('game_id', flat=True)
    
    if len(liked_games) == 0:
        # 아직 좋아하는 게임이 없음 -> JSON 인기 게임 (이미 평가한 것 제외)
        return {
            'needs_onboarding': False,
            'recommendations': format_json_games(popular_from_json, 75, rated_steam_ids),
            'method': 'popular_json_filtered',
            'message': '아직 좋아하는 게임이 없네요. 마음에 드는 게임에 👍를 눌러주세요!'
        }
    
    # 3. Item-Based CF 시도 (DB 기반) - 정규화된 스키마 사용
    # ※ 새 스키마: game_a_id < game_b_id 로 정규화되어 저장됨
    try:
        # 유저가 좋아한 게임의 평점을 가중치로 사용
        liked_ratings = {r.game_id: r.score for r in user_ratings.filter(score__gte=3.5)}
        liked_game_ids = list(liked_ratings.keys())
        
        # 각 후보 게임에 대해 가중 점수 계산
        # weighted_score = Σ(similarity * normalized_rating) / Σ(normalized_rating)
        from collections import defaultdict
        candidate_scores = defaultdict(lambda: {'weighted_sum': 0, 'weight_sum': 0})
        
        # 평점 정규화 함수 (비선형 → 선형)
        def normalize_rating(score):
            """3.5 → 0.7, 5 → 1.0"""
            return {3.5: 0.7, 5: 1.0}.get(score, score / 5.0)
        
        # 정규화된 스키마에서는 양방향 쿼리 필요:
        # 1) liked_game이 game_a에 있는 경우 → game_b가 추천 후보
        # 2) liked_game이 game_b에 있는 경우 → game_a가 추천 후보
        
        # 쿼리 1: liked_game이 game_a 위치
        similarities_a = GameSimilarity.objects.filter(
            game_a_id__in=liked_game_ids,
            similarity_rank__lte=30  # Top-K 최적화
        ).exclude(
            game_b_id__in=rated_game_ids
        ).values('game_a_id', 'game_b_id', 'similarity_score')
        
        for sim in similarities_a:
            liked_game_id = sim['game_a_id']
            candidate_game_id = sim['game_b_id']
            similarity = sim['similarity_score']
            user_rating = normalize_rating(liked_ratings.get(liked_game_id, 3.5))
            
            candidate_scores[candidate_game_id]['weighted_sum'] += similarity * user_rating
            candidate_scores[candidate_game_id]['weight_sum'] += user_rating
        
        # 쿼리 2: liked_game이 game_b 위치
        similarities_b = GameSimilarity.objects.filter(
            game_b_id__in=liked_game_ids,
            similarity_rank__lte=30
        ).exclude(
            game_a_id__in=rated_game_ids
        ).values('game_a_id', 'game_b_id', 'similarity_score')
        
        for sim in similarities_b:
            liked_game_id = sim['game_b_id']
            candidate_game_id = sim['game_a_id']
            similarity = sim['similarity_score']
            user_rating = normalize_rating(liked_ratings.get(liked_game_id, 3.5))
            
            candidate_scores[candidate_game_id]['weighted_sum'] += similarity * user_rating
            candidate_scores[candidate_game_id]['weight_sum'] += user_rating
        
        # 가중 평균 계산 및 정렬
        scored_games = []
        for game_id, scores in candidate_scores.items():
            if scores['weight_sum'] > 0:
                weighted_avg = scores['weighted_sum'] / scores['weight_sum']
                scored_games.append((game_id, weighted_avg))
        
        scored_games.sort(key=lambda x: x[1], reverse=True)
        top_game_ids = [g[0] for g in scored_games[:limit]]
        
        if top_game_ids:
            games = Game.objects.filter(id__in=top_game_ids)
            # 정렬 순서 유지
            game_dict = {g.id: g for g in games}
            ordered_games = [game_dict[gid] for gid in top_game_ids if gid in game_dict]
            db_recommendations = format_db_games(ordered_games, 85)
            
            if len(db_recommendations) >= limit // 2:
                return {
                    'needs_onboarding': False,
                    'recommendations': db_recommendations,
                    'method': 'item_based_cf',
                    'message': f'좋아하신 게임과 비슷한 게임을 추천해드려요!'
                }
    except Exception as e:
        logger.error(f"Item-based CF failed: {e}")
    
    # 4. 장르 기반 추천 시도 (Content-Based)
    try:
        liked_game_objs = Game.objects.filter(id__in=liked_games)
        liked_genres = set()
        for game in liked_game_objs:
            if game.genre:
                liked_genres.update(game.genre.split(','))
        
        if liked_genres:
            genre_filter = Q()
            for genre in liked_genres:
                genre_filter |= Q(genre__icontains=genre.strip())
            
            similar_by_genre = Game.objects.filter(genre_filter).exclude(
                id__in=rated_game_ids
            ).order_by('-metacritic_score')[:limit]
            
            db_recommendations = format_db_games(similar_by_genre, 75)
            
            if len(db_recommendations) >= limit // 2:
                return {
                    'needs_onboarding': False,
                    'recommendations': db_recommendations,
                    'method': 'content_based',
                    'message': f'좋아하시는 장르({", ".join(list(liked_genres)[:3])})의 게임을 추천해드려요!'
                }
    except Exception as e:
        logger.error(f"Content-based failed: {e}")
    
    # 5. 최후의 폴백: JSON 인기 게임 (항상 성공)
    return {
        'needs_onboarding': False,
        'recommendations': format_json_games(popular_from_json, 70, rated_steam_ids),
        'method': 'popular_json_fallback',
        'message': '인기 게임을 추천해드려요! 더 많은 게임을 평가하면 맞춤 추천이 정확해져요.'
    }


def save_user_rating(user, game_id, score, is_onboarding=False):
    """
    사용자 평가 저장
    
    Args:
        user: User 객체
        game_id: 게임 ID (RAWG ID 또는 DB ID)
        score: 점수 (-1, 0, 3.5, 5)
        is_onboarding: 온보딩 평가 여부
    
    Returns:
        GameRating 객체
    """
    from .models import GameRating, OnboardingStatus
    from games.models import Game
    
    # 게임 찾기 (RAWG ID로 먼저 시도)
    try:
        game = Game.objects.get(rawg_id=game_id)
    except Game.DoesNotExist:
        try:
            game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            # 게임이 DB에 없으면 생성 (최소 정보만)
            game = Game.objects.create(
                rawg_id=game_id,
                title=f"Game {game_id}",
                genre="Unknown"
            )
    
    # 평가 생성 또는 업데이트
    rating, created = GameRating.objects.update_or_create(
        user=user,
        game=game,
        defaults={
            'score': score,
            'is_onboarding': is_onboarding
        }
    )
    
    # 온보딩 상태 업데이트
    if is_onboarding:
        status, _ = OnboardingStatus.objects.get_or_create(user=user)
        if status.status == 'not_started':
            status.status = 'in_progress'
            status.started_at = timezone.now()
        status.total_ratings = GameRating.objects.filter(user=user).count()
        status.save()
    
    return rating


def complete_onboarding(user, skipped=False):
    """
    온보딩 완료 처리
    
    Args:
        user: User 객체
        skipped: 스킵 여부
    """
    from .models import OnboardingStatus
    
    status, _ = OnboardingStatus.objects.get_or_create(user=user)
    status.status = 'skipped' if skipped else 'completed'
    status.completed_at = timezone.now()
    status.save()
    
    return status
