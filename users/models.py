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
    
    # 추천 시스템을 위한 유사 유저 목록 (Many-to-Many)
    similar_users = models.ManyToManyField('self', blank=True)

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