from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, GameRating, GameSimilarity, UserSimilarity, OnboardingStatus, SteamLibraryCache

# 커스텀 유저 모델을 관리자 페이지에 등록
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 관리자 목록 화면에 보일 필드들
    list_display = ('username', 'email', 'nickname', 'is_steam_linked', 'is_staff')
    
    # 상세 수정 화면에 보일 필드 그룹핑
    fieldsets = UserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('nickname', 'avatar', 'steam_id', 'is_steam_linked')}),
    )


@admin.register(GameRating)
class GameRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'score', 'is_onboarding', 'created_at')
    list_filter = ('score', 'is_onboarding')
    search_fields = ('user__username', 'game__title')
    ordering = ('-created_at',)


@admin.register(GameSimilarity)
class GameSimilarityAdmin(admin.ModelAdmin):
    list_display = ('game_a', 'game_b', 'similarity_score', 'similarity_rank', 'calculated_at')
    list_filter = ('similarity_rank',)
    search_fields = ('game_a__title', 'game_b__title')
    ordering = ('-similarity_score',)


@admin.register(UserSimilarity)
class UserSimilarityAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'similarity_score', 'calculated_at')
    search_fields = ('from_user__username', 'to_user__username')
    ordering = ('-similarity_score',)


@admin.register(OnboardingStatus)
class OnboardingStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'total_ratings', 'started_at', 'completed_at')
    list_filter = ('status',)
    search_fields = ('user__username',)


@admin.register(SteamLibraryCache)
class SteamLibraryCacheAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_games', 'total_playtime_hours', 'last_updated')
    search_fields = ('user__username',)