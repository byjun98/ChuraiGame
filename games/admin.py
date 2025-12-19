from django.contrib import admin
from .models import Game, Rating, GameScreenshot, GameTrailer, Tag

class GameScreenshotInline(admin.TabularInline):
    model = GameScreenshot
    extra = 0

class GameTrailerInline(admin.TabularInline):
    model = GameTrailer
    extra = 0


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'tag_type', 'weight']
    list_filter = ['tag_type']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'genre', 'steam_appid', 'rawg_id', 'metacritic_score', 'tag_list']
    list_filter = ['genre', 'tags']
    search_fields = ['title', 'steam_appid']
    filter_horizontal = ['tags']  # 태그 선택 UI 개선
    inlines = [GameScreenshotInline, GameTrailerInline]
    readonly_fields = ['steam_appid']
    
    def tag_list(self, obj):
        return ", ".join([t.name for t in obj.tags.all()[:5]])
    tag_list.short_description = "태그"

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
