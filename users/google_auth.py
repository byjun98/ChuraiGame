"""
Google OAuth2 인증 모듈

.env 파일에 다음 환경변수 필요:
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET

Google Cloud Console 설정:
1. https://console.cloud.google.com/ 접속
2. APIs & Services > Credentials > Create OAuth 2.0 Client ID
3. Authorized redirect URIs에 추가:
   - http://localhost:8000/users/google/callback/
   - http://127.0.0.1:8000/users/google/callback/
"""

import os
import requests
import secrets
from urllib.parse import urlencode
from django.conf import settings

# Google OAuth2 Endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

def get_google_client_id():
    return os.getenv('GOOGLE_CLIENT_ID')

def get_google_client_secret():
    return os.getenv('GOOGLE_CLIENT_SECRET')


def get_google_auth_url(request, redirect_uri):
    """
    Google 로그인 URL 생성
    
    Args:
        request: Django request 객체 (state 저장용)
        redirect_uri: 콜백 URL
        
    Returns:
        str: Google OAuth 로그인 URL
    """
    client_id = get_google_client_id()
    if not client_id:
        raise ValueError("GOOGLE_CLIENT_ID가 설정되지 않았습니다.")
    
    # CSRF 방지용 state 생성
    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'state': state,
        'prompt': 'select_account',  # 항상 계정 선택 화면 표시
    }
    
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code, redirect_uri):
    """
    Authorization code를 access token으로 교환
    
    Args:
        code: Google에서 받은 authorization code
        redirect_uri: 콜백 URL (인증 시 사용한 것과 동일해야 함)
        
    Returns:
        dict: access_token, refresh_token 등 포함
    """
    client_id = get_google_client_id()
    client_secret = get_google_client_secret()
    
    if not client_id or not client_secret:
        raise ValueError("Google OAuth 설정이 완료되지 않았습니다.")
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }
    
    response = requests.post(GOOGLE_TOKEN_URL, data=data, timeout=10)
    
    if response.status_code != 200:
        raise Exception(f"Token 교환 실패: {response.text}")
    
    return response.json()


def get_google_user_info(access_token):
    """
    Access token으로 Google 사용자 정보 조회
    
    Args:
        access_token: Google access token
        
    Returns:
        dict: {
            'id': 'google_user_id',
            'email': 'user@gmail.com',
            'name': '사용자 이름',
            'picture': '프로필 이미지 URL',
            'verified_email': True/False
        }
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(GOOGLE_USERINFO_URL, headers=headers, timeout=10)
    
    if response.status_code != 200:
        raise Exception(f"사용자 정보 조회 실패: {response.text}")
    
    return response.json()


def verify_state(request, state):
    """
    CSRF 방지용 state 검증
    
    Args:
        request: Django request 객체
        state: Google에서 받은 state 값
        
    Returns:
        bool: 검증 성공 여부
    """
    saved_state = request.session.get('google_oauth_state')
    if not saved_state or saved_state != state:
        return False
    
    # 사용 후 삭제 (일회용)
    del request.session['google_oauth_state']
    return True
