from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('posts/', views.post_list_create, name='post-list'),
    path('posts/<int:post_id>/', views.post_detail, name='post-detail'),
    path('posts/<int:post_id>/like/', views.post_like, name='post-like'),
    path('posts/<int:post_id>/comments/', views.comment_create, name='comment-create'),
    path('posts/<int:post_id>/comments/<int:comment_id>/', views.comment_delete, name='comment-delete'),
]