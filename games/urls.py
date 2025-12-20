from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    # Search by title (for sale games - must be before game_id catch-all)
    path('search/', views.game_search_by_title, name='search_by_title'),
    
    # Game Detail & Management (수정: str로 변경하여 app123, bundle456 등 지원)
    path('<str:game_id>/', views.game_detail, name='detail'),
    path('<str:game_id>/wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
    
    # API Endpoints - RAWG Search & Classification
    path('api/search/', views.api_search_games, name='api_search_games'),
    path('api/genres/', views.api_get_genres, name='api_get_genres'),
    path('api/platforms/', views.api_get_platforms, name='api_get_platforms'),
    path('api/genre/<str:genre_slug>/', views.api_games_by_genre, name='api_games_by_genre'),
    
    # API Endpoints - Popular & Trending Games
    path('api/popular/', views.api_popular_games, name='api_popular_games'),
    path('api/top-rated/', views.api_top_rated_games, name='api_top_rated_games'),
    path('api/trending/', views.api_trending_games, name='api_trending_games'),
    path('api/new-releases/', views.api_new_releases, name='api_new_releases'),
    path('api/upcoming/', views.api_upcoming_games, name='api_upcoming_games'),
    path('api/ordered/', views.api_games_by_ordering, name='api_games_by_ordering'),

    # API Endpoints - Translate Game Description
    path('api/translate/', views.api_translate_game, name='api_translate_game'),

    # API Endpoints - Existing (Generic Catch-all should be last)
    path('api/wishlist/', views.api_wishlist_list, name='api_wishlist_list'),
    path('api/<str:game_id>/wishlist/toggle/', views.api_toggle_wishlist, name='api_toggle_wishlist'),
    path('api/<str:game_id>/', views.api_game_detail, name='api_game_detail'),
    
    # API Endpoints - Reviews for RAWG Games
    path('api/reviews/<int:rawg_id>/', views.api_reviews_by_rawg_id, name='api_reviews_by_rawg_id'),
    path('api/reviews/<int:rawg_id>/submit/', views.api_submit_review_by_rawg_id, name='api_submit_review'),
    
    # API Endpoints - Wishlist for RAWG Games (RAWG ID 기반 찜하기 - 자동 게임 생성)
    path('api/wishlist/<int:rawg_id>/toggle/', views.api_toggle_wishlist_by_rawg_id, name='api_toggle_wishlist_rawg'),
]