from django.contrib import admin
from .models import Game, Rating, GameScreenshot, GameTrailer, Tag, SteamReview

class GameScreenshotInline(admin.TabularInline):
    model = GameScreenshot
    extra = 0

class GameTrailerInline(admin.TabularInline):
    model = GameTrailer
    extra = 0

class SteamReviewInline(admin.TabularInline):
    model = SteamReview
    extra = 0
    readonly_fields = ['steam_review_id', 'steam_author_id', 'content', 'is_recommended', 
                       'votes_up', 'author_playtime_hours', 'crawled_at']
    can_delete = True
    max_num = 10  # 인라인으로 최대 10개만 보여주기


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'tag_type', 'weight']
    list_filter = ['tag_type']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'genre', 'steam_appid', 'rawg_id', 'metacritic_score', 'tag_list', 'review_count']
    list_filter = ['genre', 'tags']
    search_fields = ['title', 'steam_appid']
    filter_horizontal = ['tags']  # 태그 선택 UI 개선
    inlines = [GameScreenshotInline, GameTrailerInline, SteamReviewInline]
    readonly_fields = ['steam_appid']
    
    def tag_list(self, obj):
        return ", ".join([t.name for t in obj.tags.all()[:5]])
    tag_list.short_description = "태그"
    
    def review_count(self, obj):
        return obj.steam_reviews.count()
    review_count.short_description = "Steam 리뷰"

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'game', 'score', 'created_at']
    list_filter = ['score', 'created_at']
    search_fields = ['user__username', 'game__title']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(GameScreenshot)
class GameScreenshotAdmin(admin.ModelAdmin):
    list_display = ['game', 'image_url']
    search_fields = ['game__title']

@admin.register(GameTrailer)
class GameTrailerAdmin(admin.ModelAdmin):
    list_display = ['game', 'name', 'preview_url']
    search_fields = ['game__title', 'name']


@admin.register(SteamReview)
class SteamReviewAdmin(admin.ModelAdmin):
    list_display = ['game', 'is_recommended', 'votes_up', 'author_playtime_hours', 'content_preview', 'crawled_at']
    list_filter = ['is_recommended', 'crawled_at']
    search_fields = ['game__title', 'content']
    readonly_fields = ['steam_review_id', 'steam_author_id', 'crawled_at']
    raw_id_fields = ['game']
    list_per_page = 50
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = "리뷰 내용"
