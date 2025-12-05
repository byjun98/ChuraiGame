from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('<int:game_id>/', views.game_detail, name='detail'),
    path('<int:game_id>/wishlist/', views.toggle_wishlist, name='toggle_wishlist'),
]