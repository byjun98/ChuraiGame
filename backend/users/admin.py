from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# 커스텀 유저 모델을 관리자 페이지에 등록
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 관리자 목록 화면에 보일 필드들
    list_display = ('username', 'email', 'nickname', 'is_steam_linked', 'is_staff')
    
    # 상세 수정 화면에 보일 필드 그룹핑
    fieldsets = UserAdmin.fieldsets + (
        ('추가 정보', {'fields': ('nickname', 'avatar', 'steam_id', 'is_steam_linked')}),
    )