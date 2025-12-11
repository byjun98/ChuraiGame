from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.contrib import messages
import json
import os
from django.conf import settings

from .forms import SignupForm, CustomLoginForm
from .models import User
from .steam_auth import (
    get_steam_login_url,
    validate_steam_login,
    get_steam_user_info,
    get_steam_owned_games,
    get_steam_recently_played,
    get_game_recommendations_from_library
)
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
    # JSON 파일에서 게임 데이터 가져오기
    try:
        json_file_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
        
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                games_data = json.load(f)
        else:
            games_data = []
            print(f"파일을 찾을 수 없습니다: {json_file_path}")

        games_json = json.dumps(games_data, cls=DjangoJSONEncoder)

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


# =============================================================================
# Steam OAuth Login Views
# =============================================================================

def steam_login(request):
    """
    Initiate Steam OpenID login
    Redirects user to Steam login page
    """
    # Build callback URL
    callback_url = request.build_absolute_uri('/users/steam/callback/')
    steam_url = get_steam_login_url(callback_url)
    
    # Store next URL if provided
    next_url = request.GET.get('next', '/')
    request.session['steam_login_next'] = next_url
    
    # Store if this is a link request (user already logged in)
    if request.user.is_authenticated:
        request.session['steam_link_mode'] = True
    else:
        request.session['steam_link_mode'] = False
    
    return redirect(steam_url)


def steam_callback(request):
    """
    Handle Steam OpenID callback
    Creates or logs in user based on Steam ID
    """
    # Validate Steam login
    steam_id = validate_steam_login(request.GET)
    
    if not steam_id:
        messages.error(request, 'Steam 로그인에 실패했습니다. 다시 시도해주세요.')
        return redirect('users:login')
    
    # Get Steam user info
    steam_info = get_steam_user_info(steam_id)
    
    # Check if this is a link request (user already logged in)
    is_link_mode = request.session.pop('steam_link_mode', False)
    next_url = request.session.pop('steam_login_next', '/')
    
    if is_link_mode and request.user.is_authenticated:
        # Link Steam account to existing user
        user = request.user
        
        # Check if Steam ID is already linked to another account
        existing_user = User.objects.filter(steam_id=steam_id).exclude(pk=user.pk).first()
        if existing_user:
            messages.error(request, '이 Steam 계정은 이미 다른 계정에 연동되어 있습니다.')
            return redirect(next_url)
        
        # Link Steam account
        user.steam_id = steam_id
        user.is_steam_linked = True
        if steam_info:
            # Optionally update avatar from Steam
            # user.avatar_url = steam_info.get('avatarfull', '')
            pass
        user.save()
        
        messages.success(request, f"Steam 계정 '{steam_info.get('personaname', steam_id)}'이(가) 연동되었습니다!")
        return redirect(next_url)
    
    else:
        # Login or register new user with Steam
        
        # Check if Steam ID already exists
        try:
            user = User.objects.get(steam_id=steam_id)
            # User exists, log them in
            login(request, user)
            messages.success(request, f"Steam으로 로그인되었습니다. 환영합니다, {user.nickname or user.username}님!")
            return redirect(next_url)
        
        except User.DoesNotExist:
            # Create new user with Steam account
            if steam_info:
                persona_name = steam_info.get('personaname', f'Steam_{steam_id[-6:]}')
                
                # Generate unique username
                base_username = f"steam_{steam_id[-8:]}"
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                # Create user
                user = User.objects.create_user(
                    username=username,
                    nickname=persona_name,
                    steam_id=steam_id,
                    is_steam_linked=True,
                )
                # Set unusable password since they'll login via Steam
                user.set_unusable_password()
                user.save()
                
                login(request, user)
                messages.success(request, f"Steam 계정으로 가입이 완료되었습니다! 환영합니다, {persona_name}님!")
                return redirect(next_url)
            else:
                messages.error(request, 'Steam 사용자 정보를 가져올 수 없습니다.')
                return redirect('users:login')


@login_required
def steam_unlink(request):
    """
    Unlink Steam account from user profile
    """
    if request.method == 'POST':
        user = request.user
        
        # Check if user has a password (can still login without Steam)
        if user.has_usable_password():
            user.steam_id = None
            user.is_steam_linked = False
            user.save()
            messages.success(request, 'Steam 계정 연동이 해제되었습니다.')
        else:
            messages.error(request, 'Steam으로만 가입한 계정입니다. 비밀번호를 설정한 후 연동 해제할 수 있습니다.')
        
        return redirect('home')
    
    return redirect('home')


@login_required
def steam_library_api(request):
    """
    API endpoint to fetch user's Steam library
    Returns owned games and recommendations
    """
    user = request.user
    
    if not user.is_steam_linked or not user.steam_id:
        return JsonResponse({
            'error': 'Steam 계정이 연동되지 않았습니다.',
            'is_linked': False
        }, status=400)
    
    # Get library and recommendations
    library_data = get_game_recommendations_from_library(user.steam_id)
    
    return JsonResponse({
        'is_linked': True,
        'steam_id': user.steam_id,
        **library_data
    })


@login_required
def steam_recently_played_api(request):
    """
    API endpoint to fetch user's recently played games
    """
    user = request.user
    
    if not user.is_steam_linked or not user.steam_id:
        return JsonResponse({
            'error': 'Steam 계정이 연동되지 않았습니다.',
            'is_linked': False
        }, status=400)
    
    recently_played = get_steam_recently_played(user.steam_id, count=20)
    
    return JsonResponse({
        'is_linked': True,
        'recently_played': recently_played
    })


@login_required
def personalized_recommendations_api(request):
    """
    API endpoint for personalized game recommendations
    Based on user's Steam library genres and tags
    
    Priority:
    1. Library genre similarity (50 points)
    2. Rating (30 points)  
    3. Sale bonus (20 points)
    """
    from .recommendation import get_personalized_recommendations, RAWG_API_KEY
    from .steam_auth import get_steam_owned_games
    
    user = request.user
    
    # Debug logging
    print(f"[DEBUG] personalized_recommendations_api called")
    print(f"[DEBUG] User: {user.email}, Steam linked: {user.is_steam_linked}, Steam ID: {user.steam_id}")
    print(f"[DEBUG] RAWG_API_KEY loaded: {bool(RAWG_API_KEY)}, length: {len(RAWG_API_KEY) if RAWG_API_KEY else 0}")
    
    # Check if Steam is linked
    if not user.is_steam_linked or not user.steam_id:
        print(f"[DEBUG] Steam not linked, returning early")
        return JsonResponse({
            'is_personalized': False,
            'recommendations': [],
            'message': 'Steam 연동 후 개인화 추천을 받을 수 있습니다.',
            'genres_analysis': None
        })
    
    # Get user's Steam library
    steam_library = get_steam_owned_games(user.steam_id)
    print(f"[DEBUG] Steam library fetched: {len(steam_library) if steam_library else 0} games")
    
    if not steam_library:
        print(f"[DEBUG] No Steam library, returning early")
        return JsonResponse({
            'is_personalized': False,
            'recommendations': [],
            'message': 'Steam 라이브러리를 가져올 수 없습니다. 프로필이 공개 상태인지 확인해주세요.',
            'genres_analysis': None
        })
    
    # Get sale games from JSON file
    try:
        json_file_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as f:
                sale_games = json.load(f)
        else:
            sale_games = []
    except Exception as e:
        sale_games = []
        print(f"Error loading sale data: {e}")
    
    print(f"[DEBUG] Sale games loaded: {len(sale_games)}")
    
    # Generate recommendations (250 for infinite scroll)
    result = get_personalized_recommendations(
        steam_library=steam_library,
        sale_games=sale_games,
        limit=250
    )
    
    print(f"[DEBUG] Recommendations generated: {len(result.get('recommendations', []))} games")
    print(f"[DEBUG] Is personalized: {result.get('is_personalized')}")
    print(f"[DEBUG] Message: {result.get('message')}")
    
    return JsonResponse(result)