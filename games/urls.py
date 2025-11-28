from django.urls import path
from . import views

app_name = 'games'

# 아직 뷰가 없더라도 빈 리스트라도 있어야 에러가 안 납니다.
urlpatterns = [
    # 나중에 게임 상세 페이지 등이 생기면 여기에 추가
    # path('detail/<int:game_id>/', views.detail, name='detail'),
]