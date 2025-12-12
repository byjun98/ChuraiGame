"""
URL configuration for ChuraiGame backend.
Vue.js 프론트엔드와 연동되는 API 서버
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# JWT Token Views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ===== API 엔드포인트 =====
    # JWT 인증
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 사용자 관련 API
    path('api/auth/', include('users.api_urls')),
    
    # 게임 관련 API
    path('api/games/', include('games.urls')),
    
    # 커뮤니티 API
    path('api/community/', include('community.urls')),
    
    # ===== 기존 HTML 뷰 (레거시 지원) =====
    path('users/', include('users.urls')),
    path('games-html/', include('games.urls')),  # HTML 버전은 games-html로
    path('community-html/', include('community.urls')),
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)