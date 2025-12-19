from django.db import models
from django.conf import settings


class Tag(models.Model):
    """
    게임 태그/장르 테이블
    
    장르 문자열을 그대로 쓰지 않고 별도 테이블로 분리하여:
    - 가중치 부여 가능
    - 태그 간 유사도 계산 가능
    - 장르 기반 필터링 최적화
    
    사용 예시:
        action = Tag.objects.get(slug='action')
        rpg_games = Game.objects.filter(tags__slug='rpg')
    """
    TAG_TYPES = [
        ('genre', '장르'),        # Action, RPG, Strategy 등
        ('theme', '테마'),        # Sci-Fi, Fantasy, Horror 등
        ('feature', '특징'),      # Multiplayer, Open World 등
        ('mood', '분위기'),       # Relaxing, Challenging 등
    ]
    
    name = models.CharField("태그명", max_length=50)
    slug = models.SlugField("슬러그", unique=True, help_text='URL/검색용 영문 식별자')
    tag_type = models.CharField("태그 유형", max_length=20, choices=TAG_TYPES, default='genre')
    weight = models.FloatField("가중치", default=1.0, help_text='추천 계산 시 중요도 (기본 1.0)')
    
    class Meta:
        verbose_name = "태그"
        verbose_name_plural = "태그"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['tag_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_tag_type_display()})"


class Game(models.Model):
    """
    게임 기본 정보
    
    벡터화 전략 (하이브리드 추천):
    - 협업 필터링: GameRating 기반 임베딩
    - 콘텐츠 기반: tags (M:N), metacritic_score
    - 메타데이터: description (텍스트 임베딩용)
    """
    steam_appid = models.IntegerField(unique=True, null=True)  # 스팀 연동용
    title = models.CharField(max_length=200)
    
    # 기존 genre 필드 (하위 호환성 유지, 마이그레이션용)
    genre = models.CharField(max_length=100, blank=True, help_text='레거시 필드. tags 사용 권장')
    
    # 새로운 태그 시스템 (M:N)
    tags = models.ManyToManyField(
        Tag, 
        related_name='games', 
        blank=True,
        help_text='장르/테마/특징 태그 (추천 계산에 사용)'
    )
    
    image_url = models.URLField()
    rawg_id = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    background_image = models.URLField(max_length=500, blank=True)
    metacritic_score = models.IntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = "게임"
        verbose_name_plural = "게임"
        indexes = [
            models.Index(fields=['steam_appid']),
            models.Index(fields=['rawg_id']),
            models.Index(fields=['metacritic_score']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_tag_vector(self):
        """
        게임의 태그 벡터 반환 (장르 유사도 계산용)
        
        Returns:
            dict: {tag_slug: weight, ...}
        """
        return {tag.slug: tag.weight for tag in self.tags.all()}
    
    @staticmethod
    def calculate_tag_similarity(game_a, game_b):
        """
        두 게임 간 태그 유사도 계산 (Jaccard with weights)
        
        Returns:
            float: 0~1 범위의 유사도
        """
        tags_a = set(game_a.tags.values_list('slug', flat=True))
        tags_b = set(game_b.tags.values_list('slug', flat=True))
        
        if not tags_a or not tags_b:
            return 0.0
        
        intersection = len(tags_a & tags_b)
        union = len(tags_a | tags_b)
        
        return intersection / union if union > 0 else 0.0

class GameScreenshot(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='screenshots')
    image_url = models.URLField(max_length=500)

class GameTrailer(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='trailers')
    name = models.CharField(max_length=200)
    preview_url = models.URLField(max_length=500)
    data_480 = models.URLField(max_length=500)
    data_max = models.URLField(max_length=500)

class CachedGameList(models.Model):
    """
    RAWG API 응답을 캐싱하여 로딩 속도 향상
    카테고리별로 게임 목록을 JSON으로 저장
    """
    CATEGORY_CHOICES = [
        ('popular', '요즘 뜨는'),
        ('top_rated', '평점 높은'),
        ('new_releases', '신작 게임'),
        ('trending', '트렌딩'),
        ('upcoming', '출시 예정'),
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    games_data = models.JSONField(default=list)  # 게임 목록 JSON
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Cached Game List'
        verbose_name_plural = 'Cached Game Lists'
    
    def __str__(self):
        return f"{self.get_category_display()} ({len(self.games_data)} games)"
    
    @classmethod
    def get_cached_games(cls, category, max_age_hours=6):
        """
        캐시된 게임 목록 가져오기
        max_age_hours 이내의 캐시만 유효
        """
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            cache = cls.objects.get(category=category)
            age = timezone.now() - cache.updated_at
            if age < timedelta(hours=max_age_hours):
                return cache.games_data
        except cls.DoesNotExist:
            pass
        return None
    
    @classmethod
    def set_cached_games(cls, category, games_data):
        """캐시 저장/업데이트"""
        cache, created = cls.objects.update_or_create(
            category=category,
            defaults={'games_data': games_data}
        )
        return cache


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    score = models.FloatField() # 1.0 ~ 5.0
    content = models.TextField(blank=True) # 리뷰 내용
    playtime_forever = models.IntegerField(default=0) # 스팀에서 가져온 플레이 타임 (분)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'game') # 한 유저는 한 게임에 하나의 평가만
