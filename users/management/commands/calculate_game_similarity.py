"""
게임 유사도 배치 계산 Management Command

사용법:
    python manage.py calculate_game_similarity
    python manage.py calculate_game_similarity --min-ratings 5
    python manage.py calculate_game_similarity --top-k 30

배치 스케줄링 (cron):
    # 매일 새벽 3시에 실행
    0 3 * * * cd /path/to/project && python manage.py calculate_game_similarity

알고리즘:
    1. 모든 GameRating 데이터를 유저-게임 행렬로 변환
    2. 평점 정규화: -1→-1.0, 0→0.0, 3.5→0.7, 5→1.0
    3. 게임 벡터 = 해당 게임을 평가한 유저들의 정규화 점수 벡터
    4. 게임 간 코사인 유사도 계산 (희소 행렬 활용)
    5. 정규화 저장: game_a_id < game_b_id (저장 공간 50% 절약)
    6. similarity_rank 계산 (Top-K 쿼리 최적화)
"""

import time
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db import transaction
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


# 평점 정규화 맵핑 (비선형 스케일 → 선형 스케일)
SCORE_NORMALIZATION = {
    -1: -1.0,   # 역따봉 → -1.0
    0: 0.0,     # 스킵 → 0.0 (실제로는 필터링됨)
    3.5: 0.7,   # 따봉 → 0.7
    5: 1.0,     # 쌍따봉 → 1.0
}


def normalize_score(score):
    """
    평점을 정규화된 값으로 변환
    
    원본 스케일: -1, 0, 3.5, 5 (비선형)
    정규화 스케일: -1.0 ~ 1.0 (선형)
    """
    return SCORE_NORMALIZATION.get(score, score / 5.0)


class Command(BaseCommand):
    help = '게임 간 유사도를 계산하여 GameSimilarity 테이블에 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-ratings',
            type=int,
            default=3,
            help='최소 평가 수 (이보다 적은 평가를 받은 게임은 제외, 기본값: 3)'
        )
        parser.add_argument(
            '--top-k',
            type=int,
            default=50,
            help='각 게임마다 저장할 유사 게임 수 (기본값: 50)'
        )
        parser.add_argument(
            '--min-similarity',
            type=float,
            default=0.1,
            help='저장할 최소 유사도 (기본값: 0.1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 저장 없이 통계만 출력'
        )

    def handle(self, *args, **options):
        from users.models import GameRating, GameSimilarity
        from games.models import Game
        
        min_ratings = options['min_ratings']
        top_k = options['top_k']
        min_similarity = options['min_similarity']
        dry_run = options['dry_run']
        
        start_time = time.time()
        
        self.stdout.write(self.style.NOTICE('===== 게임 유사도 배치 계산 시작 ====='))
        self.stdout.write(f'설정: min_ratings={min_ratings}, top_k={top_k}, min_similarity={min_similarity}')
        
        # 1. 평가 데이터 로드
        self.stdout.write('\n[1/6] 평가 데이터 로드 중...')
        ratings = list(GameRating.objects.filter(
            score__gt=0  # 0점(스킵) 제외
        ).values('user_id', 'game_id', 'score'))
        
        if len(ratings) < 10:
            self.stdout.write(self.style.WARNING(
                f'평가 데이터가 너무 적습니다 ({len(ratings)}개). '
                '최소 10개 이상의 평가가 필요합니다.'
            ))
            return
        
        self.stdout.write(f'  총 {len(ratings)}개의 평가 데이터 로드 완료')
        
        # 2. DataFrame 생성 및 필터링
        self.stdout.write('\n[2/6] 데이터 전처리 중...')
        df = pd.DataFrame(ratings)
        
        # 평점 정규화 적용
        df['normalized_score'] = df['score'].apply(normalize_score)
        self.stdout.write(f'  평점 정규화 완료: {dict(df.groupby("score")["normalized_score"].first())}')
        
        # 게임별 평가 수 계산
        game_rating_counts = df.groupby('game_id').size()
        valid_games = game_rating_counts[game_rating_counts >= min_ratings].index.tolist()
        
        # 유효한 게임만 필터링
        df = df[df['game_id'].isin(valid_games)]
        
        unique_users = df['user_id'].nunique()
        unique_games = df['game_id'].nunique()
        
        self.stdout.write(f'  유저 수: {unique_users}명')
        self.stdout.write(f'  게임 수: {unique_games}개 (최소 {min_ratings}개 이상 평가받은 게임)')
        self.stdout.write(f'  필터링 후 평가 수: {len(df)}개')
        
        if unique_games < 2:
            self.stdout.write(self.style.WARNING('유사도를 계산할 게임이 충분하지 않습니다.'))
            return
        
        # 3. 희소 행렬 생성
        self.stdout.write('\n[3/6] 희소 행렬 생성 중...')
        
        # Category 코드로 변환하여 효율적으로 인덱싱
        user_cat = df['user_id'].astype('category')
        game_cat = df['game_id'].astype('category')
        
        user_codes = user_cat.cat.codes.values
        game_codes = game_cat.cat.codes.values
        scores = df['normalized_score'].values  # 정규화된 점수 사용
        
        # 희소 행렬 (행: 게임, 열: 유저, 값: 정규화된 점수)
        sparse_matrix = csr_matrix(
            (scores, (game_codes, user_codes)),
            shape=(len(game_cat.cat.categories), len(user_cat.cat.categories))
        )
        
        sparsity = 1 - (sparse_matrix.nnz / (sparse_matrix.shape[0] * sparse_matrix.shape[1]))
        self.stdout.write(f'  행렬 크기: {sparse_matrix.shape[0]} 게임 x {sparse_matrix.shape[1]} 유저')
        self.stdout.write(f'  희소성: {sparsity:.2%} (0이 아닌 값: {sparse_matrix.nnz}개)')
        
        # 4. 코사인 유사도 계산
        self.stdout.write('\n[4/6] 게임 간 코사인 유사도 계산 중...')
        similarity_matrix = cosine_similarity(sparse_matrix)
        
        self.stdout.write(f'  유사도 행렬 크기: {similarity_matrix.shape}')
        
        # 5. 정규화 및 랭크 계산
        self.stdout.write('\n[5/6] 유사도 정규화 및 랭크 계산 중...')
        self.stdout.write('  📌 규칙: game_a_id < game_b_id (저장 공간 50% 절약)')
        
        game_ids = game_cat.cat.categories.tolist()
        
        # 각 게임 기준 Top-K 유사 게임과 랭크 저장
        # 정규화: (min_id, max_id) 쌍으로 저장
        # 동일 쌍이 여러 번 나올 수 있으므로 max score와 min rank 유지
        pair_data = {}  # (game_a_id, game_b_id) -> {'score': float, 'rank_a': int, 'rank_b': int}
        
        for i, game_x_id in enumerate(game_ids):
            sim_scores = similarity_matrix[i]
            
            # Top-K 인덱스 (자기 자신 제외, 정렬된 순서)
            sorted_indices = np.argsort(sim_scores)[::-1]
            
            rank = 0
            for j in sorted_indices:
                if i == j:
                    continue
                    
                score = sim_scores[j]
                if score < min_similarity:
                    break  # 정렬되어 있으므로 이후는 모두 미달
                
                rank += 1
                if rank > top_k:
                    break
                
                game_y_id = game_ids[j]
                
                # 정규화: 항상 작은 ID를 game_a로
                game_a_id = min(game_x_id, game_y_id)
                game_b_id = max(game_x_id, game_y_id)
                pair_key = (game_a_id, game_b_id)
                
                if pair_key not in pair_data:
                    pair_data[pair_key] = {
                        'score': score,
                        'rank': rank  # 처음 발견된 순위 (더 작은 값 = 더 유사)
                    }
                else:
                    # 이미 존재하면 더 좋은 랭크 유지
                    pair_data[pair_key]['rank'] = min(pair_data[pair_key]['rank'], rank)
        
        # GameSimilarity 객체 생성
        similarities_to_create = []
        for (game_a_id, game_b_id), data in pair_data.items():
            similarities_to_create.append({
                'game_a_id': game_a_id,
                'game_b_id': game_b_id,
                'similarity_score': float(data['score']),
                'similarity_rank': data['rank']
            })
        
        self.stdout.write(f'  정규화된 유사도 쌍: {len(similarities_to_create)}개')
        self.stdout.write(f'  (중복 제거로 약 50% 절약)')
        
        # 통계 출력
        if similarities_to_create:
            scores = [s['similarity_score'] for s in similarities_to_create]
            ranks = [s['similarity_rank'] for s in similarities_to_create]
            self.stdout.write(f'  평균 유사도: {np.mean(scores):.4f}')
            self.stdout.write(f'  최대 유사도: {np.max(scores):.4f}')
            self.stdout.write(f'  최소 유사도: {np.min(scores):.4f}')
            self.stdout.write(f'  평균 랭크: {np.mean(ranks):.1f}')
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('\n[DRY RUN] 실제 저장 없이 종료합니다.'))
            return
        
        # 6. 트랜잭션으로 안전하게 저장
        self.stdout.write('\n[6/6] 데이터베이스에 저장 중...')
        try:
            with transaction.atomic():
                # 기존 데이터 삭제
                deleted_count, _ = GameSimilarity.objects.all().delete()
                self.stdout.write(f'  기존 레코드 {deleted_count}개 삭제')
                
                # 벌크 생성
                GameSimilarity.objects.bulk_create([
                    GameSimilarity(
                        game_a_id=s['game_a_id'],
                        game_b_id=s['game_b_id'],
                        similarity_score=s['similarity_score'],
                        similarity_rank=s['similarity_rank']
                    ) for s in similarities_to_create
                ], batch_size=1000)
                
                self.stdout.write(f'  새 레코드 {len(similarities_to_create)}개 생성')
            
            elapsed = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ 게임 유사도 계산 완료! (소요시간: {elapsed:.2f}초)'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'   - 정규화 저장: game_a_id < game_b_id ✔'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'   - 랭크 계산: similarity_rank ✔'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'   - 평점 정규화: -1→-1.0, 3.5→0.7, 5→1.0 ✔'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ 저장 실패: {e}'))
            raise
