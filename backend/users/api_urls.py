"""
users 앱의 REST API URL 설정
Vue.js 프론트엔드와 통신하는 API 엔드포인트
"""
from django.urls import path
from . import api_views

urlpatterns = [
    # 회원가입
    path('signup/', api_views.SignupView.as_view(), name='api_signup'),
    
    # 현재 사용자 정보 조회/수정
    path('user/', api_views.UserDetailView.as_view(), name='api_user'),
    
    # 로그아웃 (토큰 블랙리스트)
    path('logout/', api_views.LogoutView.as_view(), name='api_logout'),
    
    # Steam 연동
    path('link-steam/', api_views.LinkSteamView.as_view(), name='api_link_steam'),
    
    # Steam 라이브러리 조회
    path('steam-library/', api_views.SteamLibraryView.as_view(), name='api_steam_library'),
    
    # 맞춤 추천
    path('recommendations/', api_views.RecommendationsView.as_view(), name='api_recommendations'),
    
    # 온보딩 데이터
    path('onboarding/', api_views.OnboardingView.as_view(), name='api_onboarding'),
]
