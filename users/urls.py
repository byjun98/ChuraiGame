from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('delete/', views.delete_account_view, name='delete'),
    path('', views.main_view, name='main'), # 메인 페이지 뷰 필요
    
    # Steam OAuth
    path('steam/login/', views.steam_login, name='steam_login'),
    path('steam/callback/', views.steam_callback, name='steam_callback'),
    path('steam/unlink/', views.steam_unlink, name='steam_unlink'),
    
    # Steam API
    path('api/steam/library/', views.steam_library_api, name='steam_library'),
    path('api/steam/recently-played/', views.steam_recently_played_api, name='steam_recently_played'),
    
    # Recommendation API
    path('api/recommendations/', views.personalized_recommendations_api, name='recommendations'),
    
    # AI Chatbot API
    path('api/ai-chat/', views.ai_chat_api, name='ai_chat'),
    
    # Translation API
    path('api/translate/', views.translate_text_api, name='translate'),
    
    # Onboarding API (왓챠 스타일 게임 평가)
    path('api/onboarding/status/', views.onboarding_status_api, name='onboarding_status'),
    path('api/onboarding/games/', views.onboarding_games_api, name='onboarding_games'),
    path('api/onboarding/rate/', views.onboarding_rate_api, name='onboarding_rate'),
    path('api/onboarding/next-step/', views.onboarding_next_step_api, name='onboarding_next_step'),
    path('api/onboarding/complete/', views.onboarding_complete_api, name='onboarding_complete'),
    path('api/onboarding/recommendations/', views.onboarding_recommendations_api, name='onboarding_recommendations'),
    
    # Game Rating API (상세 페이지에서 사용)
    path('api/game-rating/<int:rawg_id>/', views.get_game_rating_api, name='get_game_rating'),
    
    # Avatar Upload API (프로필 사진)
    path('api/avatar/', views.avatar_upload_api, name='avatar_upload'),
    
    # Public User Profile API
    path('api/profile/<str:username>/', views.get_user_profile_api, name='get_user_profile'),
    
    # Google OAuth
    path('google/login/', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),
    path('google/unlink/', views.google_unlink, name='google_unlink'),
    
    # Naver OAuth
    path('naver/login/', views.naver_login, name='naver_login'),
    path('naver/callback/', views.naver_callback, name='naver_callback'),
    path('naver/unlink/', views.naver_unlink, name='naver_unlink'),
    
    # Genre Analysis & Steam-Style Recommendations
    path('api/genre-analysis/', views.genre_analysis_api, name='genre_analysis'),
    path('api/steam-recommendations/', views.steam_style_recommendations_api, name='steam_recommendations'),
]

