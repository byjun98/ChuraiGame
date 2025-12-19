"""
하이브리드 추천 시스템 - 유사도 계산 모듈

여러 신호를 결합한 게임 벡터 기반 추천:
1. 협업 필터링 유사도 (GameSimilarity 테이블)
2. 장르/태그 유사도 (Tag 테이블)
3. 메타크리틱 점수 유사도
4. (향후) 설명 텍스트 임베딩 유사도

최종 유사도 = 가중합:
    final_similarity = 
        0.70 * collaborative_similarity +
        0.20 * genre_similarity +
        0.10 * meta_score_similarity
"""

import logging
from django.db.models import Q
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# 가중치 설정 (튜닝 가능)
# ============================================================================

SIMILARITY_WEIGHTS = {
    'collaborative': 0.70,   # 협업 필터링 (가장 중요)
    'genre': 0.20,           # 장르/태그 유사도
    'metacritic': 0.10,      # 메타크리틱 점수 유사도
}

# 메타크리틱 점수 차이에 따른 유사도 계산 파라미터
METACRITIC_MAX_DIFF = 30  # 30점 이상 차이나면 유사도 0


# ============================================================================
# 개별 유사도 계산 함수
# ============================================================================

def get_collaborative_similarity(game_a_id: int, game_b_id: int) -> float:
    """
    협업 필터링 기반 유사도 조회 (GameSimilarity 테이블)
    
    ⚠️ 정규화된 스키마 사용: game_a_id < game_b_id
    
    Args:
        game_a_id: 게임 A ID
        game_b_id: 게임 B ID
        
    Returns:
        float: 0~1 범위의 협업 필터링 유사도 (없으면 0)
    """
    from users.models import GameSimilarity
    
    # 정규화: 항상 작은 ID를 먼저
    min_id, max_id = min(game_a_id, game_b_id), max(game_a_id, game_b_id)
    
    try:
        sim = GameSimilarity.objects.get(game_a_id=min_id, game_b_id=max_id)
        return sim.similarity_score
    except GameSimilarity.DoesNotExist:
        return 0.0


def calculate_genre_similarity(game_a, game_b) -> float:
    """
    장르/태그 유사도 계산 (Jaccard Index with weights)
    
    공식: |A ∩ B| / |A ∪ B|
    
    Args:
        game_a: Game 객체 (tags prefetch 권장)
        game_b: Game 객체
        
    Returns:
        float: 0~1 범위의 장르 유사도
    """
    tags_a = set(game_a.tags.values_list('slug', flat=True))
    tags_b = set(game_b.tags.values_list('slug', flat=True))
    
    if not tags_a and not tags_b:
        # 둘 다 태그 없으면 레거시 genre 필드 사용
        genre_a = set(g.strip().lower() for g in (game_a.genre or '').split(',') if g.strip())
        genre_b = set(g.strip().lower() for g in (game_b.genre or '').split(',') if g.strip())
        
        if not genre_a or not genre_b:
            return 0.0
        
        intersection = len(genre_a & genre_b)
        union = len(genre_a | genre_b)
        return intersection / union if union > 0 else 0.0
    
    if not tags_a or not tags_b:
        return 0.0
    
    intersection = len(tags_a & tags_b)
    union = len(tags_a | tags_b)
    
    return intersection / union if union > 0 else 0.0


def calculate_metacritic_similarity(score_a: Optional[int], score_b: Optional[int]) -> float:
    """
    메타크리틱 점수 유사도 계산
    
    점수 차이가 작을수록 유사도 높음
    
    Args:
        score_a: 게임 A의 메타크리틱 점수 (0-100)
        score_b: 게임 B의 메타크리틱 점수
        
    Returns:
        float: 0~1 범위의 점수 유사도
    """
    if score_a is None or score_b is None:
        return 0.5  # 정보 없으면 중립
    
    diff = abs(score_a - score_b)
    
    if diff >= METACRITIC_MAX_DIFF:
        return 0.0
    
    return 1 - (diff / METACRITIC_MAX_DIFF)


# ============================================================================
# 하이브리드 유사도 계산
# ============================================================================

def calculate_hybrid_similarity(
    game_a, 
    game_b,
    weights: Dict[str, float] = None
) -> Tuple[float, Dict[str, float]]:
    """
    하이브리드 유사도 계산 (여러 신호의 가중합)
    
    Args:
        game_a: Game 객체
        game_b: Game 객체
        weights: 가중치 딕셔너리 (기본값 사용 시 None)
        
    Returns:
        tuple: (final_similarity, {component_name: score, ...})
    """
    weights = weights or SIMILARITY_WEIGHTS
    
    # 1. 협업 필터링 유사도
    collab_sim = get_collaborative_similarity(game_a.id, game_b.id)
    
    # 2. 장르/태그 유사도
    genre_sim = calculate_genre_similarity(game_a, game_b)
    
    # 3. 메타크리틱 유사도
    meta_sim = calculate_metacritic_similarity(
        game_a.metacritic_score, 
        game_b.metacritic_score
    )
    
    # 가중합 계산
    final_similarity = (
        weights.get('collaborative', 0.7) * collab_sim +
        weights.get('genre', 0.2) * genre_sim +
        weights.get('metacritic', 0.1) * meta_sim
    )
    
    components = {
        'collaborative': collab_sim,
        'genre': genre_sim,
        'metacritic': meta_sim,
        'final': final_similarity
    }
    
    return final_similarity, components


def get_hybrid_recommendations(
    user,
    liked_game_ids: List[int],
    rated_game_ids: List[int],
    limit: int = 20,
    weights: Dict[str, float] = None
) -> List[Dict]:
    """
    하이브리드 추천 - 여러 유사도 신호를 결합하여 추천
    
    알고리즘:
    1. 좋아한 게임들과 유사한 게임 후보 수집 (협업 필터링)
    2. 각 후보에 대해 하이브리드 유사도 계산
    3. 평가한 게임 제외 후 정렬
    
    Args:
        user: User 객체
        liked_game_ids: 좋아한 게임 ID 리스트
        rated_game_ids: 이미 평가한 게임 ID 리스트 (제외용)
        limit: 반환할 추천 수
        weights: 유사도 가중치
        
    Returns:
        list: [{'game': Game, 'score': float, 'components': dict}, ...]
    """
    from users.models import GameSimilarity
    from games.models import Game
    
    weights = weights or SIMILARITY_WEIGHTS
    
    # 1. 협업 필터링 기반 후보 수집 (정규화된 스키마 사용)
    candidate_ids = set()
    
    # game_a 위치에 있는 경우
    sims_a = GameSimilarity.objects.filter(
        game_a_id__in=liked_game_ids,
        similarity_rank__lte=30
    ).exclude(game_b_id__in=rated_game_ids)
    
    for sim in sims_a:
        candidate_ids.add(sim.game_b_id)
    
    # game_b 위치에 있는 경우
    sims_b = GameSimilarity.objects.filter(
        game_b_id__in=liked_game_ids,
        similarity_rank__lte=30
    ).exclude(game_a_id__in=rated_game_ids)
    
    for sim in sims_b:
        candidate_ids.add(sim.game_a_id)
    
    if not candidate_ids:
        logger.info("No candidates from collaborative filtering")
        return []
    
    # 2. 후보 게임 로드 (태그 prefetch)
    candidates = Game.objects.filter(
        id__in=candidate_ids
    ).prefetch_related('tags')
    
    liked_games = Game.objects.filter(
        id__in=liked_game_ids
    ).prefetch_related('tags')
    
    # 3. 각 후보에 대해 하이브리드 유사도 계산
    candidate_scores = []
    
    for candidate in candidates:
        total_score = 0
        total_weight = 0
        best_components = None
        
        for liked_game in liked_games:
            sim, components = calculate_hybrid_similarity(
                liked_game, candidate, weights
            )
            
            # 유저 평점을 가중치로 사용할 수도 있음 (여기선 단순 평균)
            total_score += sim
            total_weight += 1
            
            if best_components is None or sim > best_components.get('final', 0):
                best_components = components
        
        if total_weight > 0:
            avg_score = total_score / total_weight
            candidate_scores.append({
                'game': candidate,
                'score': avg_score,
                'components': best_components
            })
    
    # 4. 점수 기준 정렬
    candidate_scores.sort(key=lambda x: x['score'], reverse=True)
    
    logger.info(f"Hybrid recommendations: {len(candidate_scores)} candidates, returning top {limit}")
    
    return candidate_scores[:limit]


# ============================================================================
# 장르 마이그레이션 유틸리티
# ============================================================================

def migrate_genre_to_tags():
    """
    기존 genre 문자열을 Tag 테이블로 마이그레이션
    
    사용법:
        from users.hybrid_similarity import migrate_genre_to_tags
        migrate_genre_to_tags()
    """
    from games.models import Game, Tag
    from django.utils.text import slugify
    
    games = Game.objects.exclude(genre='').exclude(genre__isnull=True)
    
    created_tags = 0
    linked_tags = 0
    
    for game in games:
        genres = [g.strip() for g in game.genre.split(',') if g.strip()]
        
        for genre_name in genres:
            slug = slugify(genre_name.lower())
            if not slug:
                continue
            
            tag, created = Tag.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': genre_name.title(),
                    'tag_type': 'genre',
                    'weight': 1.0
                }
            )
            
            if created:
                created_tags += 1
            
            if not game.tags.filter(pk=tag.pk).exists():
                game.tags.add(tag)
                linked_tags += 1
    
    logger.info(f"Migration complete: {created_tags} new tags, {linked_tags} links created")
    return {'created_tags': created_tags, 'linked_tags': linked_tags}
