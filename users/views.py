from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.serializers.json import DjangoJSONEncoder
import json

from .forms import SignupForm, CustomLoginForm
# Game 모델이 users/models.py에 정의되어 있다고 가정합니다.
# 만약 games/models.py에 있다면 'from games.models import Game'으로 변경하세요.
from games.models import Game

# --- 1. 회원가입 (Create) ---
@require_http_methods(["GET", "POST"])
def signup_view(request):
    # 이미 로그인한 사용자는 메인으로 리다이렉트
    if request.user.is_authenticated:
        return redirect('home') # 'home'은 프로젝트 urls.py에서 설정한 메인 페이지 이름

    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user) # 가입 후 자동 로그인
            return redirect('home')
    else:
        form = SignupForm()

    return render(request, 'users/signup.html', {'form': form})

# --- 2. 로그인 (Read/Auth) ---
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = CustomLoginForm()

    return render(request, 'users/login.html', {'form': form})

# --- 3. 로그아웃 ---
def logout_view(request):
    logout(request)
    return redirect('users:login')

# --- 4. 마이페이지 (Read - Detail) ---
@login_required(login_url='users:login')
def profile_view(request):
    return render(request, 'users/profile.html', {
        'user': request.user
    })

# --- 5. 회원 탈퇴 (Delete) ---
@login_required
@require_http_methods(["POST"])
def delete_account_view(request):
    if request.method == 'POST':
        request.user.delete()
        logout(request)
        return redirect('users:login')

# --- 6. 메인 페이지 (Main View) ---
@login_required(login_url='users:login')
def main_view(request):
    # DB에서 게임 데이터 가져오기
    try:
        # 필요한 필드만 가져와서 최적화 (values 사용)
        # 필드명은 실제 models.py의 Game 모델과 일치해야 합니다.
        games_queryset = Game.objects.all().values('steam_appid', 'title', 'image_url', 'genre')
        
        # 쿼리셋을 리스트로 변환 (JSON 직렬화를 위해)
        games_list = list(games_queryset)
        
        # 프론트엔드에서 사용할 키 이름으로 매핑 (선택 사항, 필요시 수정)
        # 예: steam_appid -> game_id 로 변경해서 보내고 싶다면 아래처럼 처리
        formatted_games = []
        for g in games_list:
            formatted_games.append({
                'game_id': g.get('steam_appid'),
                'title': g.get('title'),
                'thumbnail': g.get('image_url'),
                'genre': g.get('genre', 'Unknown'), # 장르가 없으면 Unknown
                'original_price': 0, # 가격 정보가 DB에 없다면 기본값
                'current_price': 0,
                'discount_rate': 0
            })

        games_json = json.dumps(formatted_games, cls=DjangoJSONEncoder)

    except Exception as e:
        print(f"게임 데이터를 불러오는 중 오류 발생: {e}")
        games_json = "[]" # 에러 발생 시 빈 배열 전달

    # Wishlist IDs
    wishlist_ids = list(request.user.wishlist.values_list('steam_appid', flat=True))
    wishlist_json = json.dumps(wishlist_ids, cls=DjangoJSONEncoder)

    return render(request, 'users/index.html', {
        'user': request.user,
        'games_json': games_json,
        'wishlist_json': wishlist_json,
    })