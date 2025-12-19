from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # 기본 필드 (username, password, email 등)는 상속받음
    
    # 프로필 관련 커스텀 필드
    nickname = models.CharField("닉네임", max_length=50, blank=True)
    avatar = models.ImageField("프로필 사진", upload_to="avatars/", null=True, blank=True)
    
    # 스팀 연동 관련
    steam_id = models.CharField("스팀 ID", max_length=50, unique=True, null=True, blank=True)
    
    # 소셜 연동 여부 플래그
    is_steam_linked = models.BooleanField(default=False)
    is_naver_linked = models.BooleanField(default=False)
    is_google_linked = models.BooleanField(default=False)
    
    # 추천 시스템을 위한 유사 유저 목록 (Many-to-Many with through model)
    # ※ 참고: 대규모 추천에서는 유저 간 유사도 계산이 O(N²)로 비효율적이므로
    #   메인 추천은 GameSimilarity(게임 간 유사도) 테이블을 사용합니다.
    #   이 필드는 SNS 팔로우 추천, 비슷한 취향의 유저 보여주기 등 보조 용도입니다.
    # 
    # UserSimilarity through 모델을 사용하여 similarity_score, calculated_at 저장
    # 직접 접근: user.similar_to_users.all() 또는 UserSimilarity.objects.filter(from_user=user)

    # 찜한 게임 목록
    wishlist = models.ManyToManyField('games.Game', related_name='wishlisted_by', blank=True)

    # --- [충돌 해결을 위한 추가 코드] ---
    # related_name을 설정하여 기본 auth.User 모델과의 충돌을 방지합니다.
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="custom_user_set",  # 여기를 수정
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set", # 여기를 수정
        related_query_name="user",
    )

    def __str__(self):
        return self.username


class SteamLibraryCache(models.Model):
    """
    Steam 라이브러리 캐시 - API 호출 최소화
    
    - 첫 로딩 시 Steam API 호출 후 DB에 저장
    - 이후 요청은 DB에서 즉시 반환 (0.01초)
    - 24시간마다 백그라운드 업데이트
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='steam_library_cache'
    )
    
    # Steam 라이브러리 데이터 (JSON)
    library_data = models.JSONField(default=list, help_text="Steam 라이브러리 게임 목록 JSON")
    
    # 통계
    total_games = models.IntegerField(default=0)
    total_playtime_hours = models.FloatField(default=0)
    
    # 캐시 관리
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Steam 라이브러리 캐시"
        verbose_name_plural = "Steam 라이브러리 캐시"
    
    def __str__(self):
        return f"{self.user.username}의 Steam 라이브러리 ({self.total_games}개)"
    
    def is_stale(self, hours=24):
        """캐시가 오래되었는지 확인 (기본 24시간)"""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() - self.last_updated > timedelta(hours=hours)


class GameRating(models.Model):
    """
    사용자 게임 평가 모델 (왓챠 스타일)
    
    점수 체계:
    - DISLIKE (-1): 역따봉 (별로예요)
    - SKIP (0): 스킵/모르겠음
    - LIKE (3.5): 따봉 (재밌어요)
    - LOVE (5): 쌍따봉 (인생게임)
    """
    RATING_CHOICES = [
        (-1, '역따봉'),
        (0, '스킵'),
        (3.5, '따봉'),
        (5, '쌍따봉'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_ratings')
    game = models.ForeignKey('games.Game', on_delete=models.CASCADE, related_name='user_ratings')
    score = models.FloatField("평점", choices=RATING_CHOICES)
    
    # 평가 소스 (온보딩 vs 일반)
    is_onboarding = models.BooleanField("온보딩 평가 여부", default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "게임 평가"
        verbose_name_plural = "게임 평가"
        unique_together = ['user', 'game']  # 한 유저가 한 게임에 하나의 평가만
        indexes = [
            models.Index(fields=['user', 'score']),
            models.Index(fields=['game', 'score']),
        ]
    
    def __str__(self):
        rating_map = {-1: '역따봉', 0: '스킵', 3.5: '따봉', 5: '쌍따봉'}
        return f"{self.user.username} - {self.game.title}: {rating_map.get(self.score, self.score)}"


class OnboardingStatus(models.Model):
    """
    사용자 온보딩 상태 추적
    
    온보딩 단계:
    1. NOT_STARTED: 시작 안함
    2. IN_PROGRESS: 진행 중
    3. COMPLETED: 완료
    4. SKIPPED: 건너뜀
    """
    STATUS_CHOICES = [
        ('not_started', '시작 안함'),
        ('in_progress', '진행 중'),
        ('completed', '완료'),
        ('skipped', '건너뜀'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onboarding_status')
    status = models.CharField("상태", max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # 진행 상황 추적
    current_step = models.IntegerField("현재 단계", default=0)  # 0: 초기, 1-5: 장르별 단계
    total_ratings = models.IntegerField("총 평가 수", default=0)
    
    # 날짜 추적
    started_at = models.DateTimeField("시작 시간", null=True, blank=True)
    completed_at = models.DateTimeField("완료 시간", null=True, blank=True)
    
    class Meta:
        verbose_name = "온보딩 상태"
        verbose_name_plural = "온보딩 상태"
    
    def __str__(self):
        return f"{self.user.username}: {self.get_status_display()}"


class GameSimilarity(models.Model):
    """
    게임 간 유사도 (미리 계산된 데이터)
    
    - 매일 배치 작업으로 계산
    - Item-Based Collaborative Filtering에 사용
    
    ⚠️ 중요 규칙 (저장 공간 최적화):
    - game_a_id < game_b_id 로 정규화하여 저장
    - (A, B, 0.8)과 (B, A, 0.8) 중복 방지
    - 저장 공간 50% 절약
    
    사용 예시:
        # 특정 게임과 유사한 Top 20 게임 조회
        GameSimilarity.objects.filter(
            Q(game_a_id=game_id) | Q(game_b_id=game_id),
            similarity_rank__lte=20
        )
    """
    game_a = models.ForeignKey(
        'games.Game', 
        on_delete=models.CASCADE, 
        related_name='similarity_from',
        help_text='항상 game_b보다 작은 ID'
    )
    game_b = models.ForeignKey(
        'games.Game', 
        on_delete=models.CASCADE, 
        related_name='similarity_to',
        help_text='항상 game_a보다 큰 ID'
    )
    similarity_score = models.FloatField("유사도 점수")  # 0 ~ 1
    
    # Top-K 쿼리 최적화용 랭크 (배치 계산 시 설정)
    similarity_rank = models.PositiveIntegerField(
        "유사도 순위", 
        default=0,
        help_text='해당 게임 기준 유사도 순위 (1이 가장 유사)',
        db_index=True
    )
    
    # 배치 관리
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "게임 유사도"
        verbose_name_plural = "게임 유사도"
        unique_together = ['game_a', 'game_b']
        indexes = [
            models.Index(fields=['game_a', 'similarity_rank']),
            models.Index(fields=['game_b', 'similarity_rank']),
            models.Index(fields=['game_a', '-similarity_score']),
            models.Index(fields=['game_b', '-similarity_score']),
        ]
        # game_a_id < game_b_id 제약은 배치 작업에서 보장
    
    def __str__(self):
        return f"{self.game_a.title} ↔ {self.game_b.title}: {self.similarity_score:.2f} (rank: {self.similarity_rank})"
    
    @staticmethod
    def normalize_game_ids(game_x_id, game_y_id):
        """
        두 게임 ID를 정규화하여 (min, max) 순서로 반환
        
        항상 game_a_id < game_b_id 규칙 적용
        """
        return (min(game_x_id, game_y_id), max(game_x_id, game_y_id))
    
    @classmethod
    def get_similar_games(cls, game_id, limit=20):
        """
        특정 게임과 유사한 게임 목록 조회 (최적화된 쿼리)
        
        Args:
            game_id: 기준 게임 ID
            limit: 반환할 유사 게임 수
            
        Returns:
            list: [(game_id, similarity_score), ...]
        """
        from django.db.models import Q, F, Case, When, Value
        
        results = cls.objects.filter(
            Q(game_a_id=game_id) | Q(game_b_id=game_id),
            similarity_rank__lte=limit
        ).values_list('game_a_id', 'game_b_id', 'similarity_score')
        
        similar = []
        for game_a_id, game_b_id, score in results:
            # 자신이 아닌 쪽의 게임 ID 반환
            other_id = game_b_id if game_a_id == game_id else game_a_id
            similar.append((other_id, score))
        
        return sorted(similar, key=lambda x: x[1], reverse=True)[:limit]


class UserSimilarity(models.Model):
    """
    유저 간 유사도 (SNS/팔로우 추천용)
    
    ⚠️ 주의: 이 테이블은 게임 추천의 핵심이 아닙니다!
    - 게임 추천: GameSimilarity 사용
    - 유저 추천: UserSimilarity 사용 (SNS, 프로필 추천 등)
    
    사용처:
    - "취향이 비슷한 유저"
    - SNS형 팔로우 추천
    - 커뮤니티 노출
    """
    from_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='similar_to_users'
    )
    to_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='similar_from_users'
    )
    similarity_score = models.FloatField("유사도 점수", default=0)  # 0 ~ 1
    calculated_at = models.DateTimeField("계산 시점", auto_now=True)
    
    class Meta:
        verbose_name = "유저 유사도"
        verbose_name_plural = "유저 유사도"
        unique_together = ['from_user', 'to_user']
        indexes = [
            models.Index(fields=['from_user', '-similarity_score']),
        ]
    
    def __str__(self):
        return f"{self.from_user.username} → {self.to_user.username}: {self.similarity_score:.2f}"

