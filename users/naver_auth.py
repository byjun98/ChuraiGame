"""
Naver OAuth2 인증 모듈

.env 파일에 다음 환경변수 필요:
- NAVER_CLIENT_ID
- NAVER_SECRET

Naver Developers 설정:
1. https://developers.naver.com/apps/ 접속
2. 애플리케이션 등록 > 네아로(네이버 아이디로 로그인)
3. Callback URL 등록:
   - http://localhost:8000/users/naver/callback/
   - http://127.0.0.1:8000/users/naver/callback/
"""

import os
import requests
import secrets
from urllib.parse import urlencode
from django.conf import settings

# Naver OAuth2 Endpoints
NAVER_AUTH_URL = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_USERINFO_URL = "https://openapi.naver.com/v1/nid/me"


def get_naver_client_id():
    return os.getenv('NAVER_CLIENT_ID')


def get_naver_client_secret():
    return os.getenv('NAVER_SECRET')


def get_naver_auth_url(request, redirect_uri):
    """
    Naver 로그인 URL 생성
    
    Args:
        request: Django request 객체 (state 저장용)
        redirect_uri: 콜백 URL
        
    Returns:
        str: Naver OAuth 로그인 URL
    """
    client_id = get_naver_client_id()
    if not client_id:
        raise ValueError("NAVER_CLIENT_ID가 설정되지 않았습니다.")
    
    # CSRF 방지용 state 생성
    state = secrets.token_urlsafe(32)
    request.session['naver_oauth_state'] = state
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'state': state,
    }
    
    return f"{NAVER_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code, state):
    """
    Authorization code를 access token으로 교환
    
    Args:
        code: Naver에서 받은 authorization code
        state: CSRF 방지용 state
        
    Returns:
        dict: access_token, refresh_token 등 포함
    """
    client_id = get_naver_client_id()
    client_secret = get_naver_client_secret()
    
    if not client_id or not client_secret:
        raise ValueError("Naver OAuth 설정이 완료되지 않았습니다.")
    
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'state': state,
        'grant_type': 'authorization_code',
    }
    
    response = requests.get(NAVER_TOKEN_URL, params=params, timeout=10)
    
    if response.status_code != 200:
        raise Exception(f"Token 교환 실패: {response.text}")
    
    result = response.json()
    
    if 'error' in result:
        raise Exception(f"Token 오류: {result.get('error_description', result.get('error'))}")
    
    return result


def get_naver_user_info(access_token):
    """
    Access token으로 Naver 사용자 정보 조회
    
    Args:
        access_token: Naver access token
        
    Returns:
        dict: {
            'id': 'naver_user_id',
            'email': 'user@naver.com',
            'nickname': '닉네임',
            'profile_image': '프로필 이미지 URL',
            'name': '실명 (선택)'
        }
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(NAVER_USERINFO_URL, headers=headers, timeout=10)
    
    if response.status_code != 200:
        raise Exception(f"사용자 정보 조회 실패: {response.text}")
    
    result = response.json()
    
    if result.get('resultcode') != '00':
        raise Exception(f"Naver API 오류: {result.get('message')}")
    
    # Naver는 response 안에 실제 데이터가 있음
    return result.get('response', {})


def verify_state(request, state):
    """
    CSRF 방지용 state 검증
    
    Args:
        request: Django request 객체
        state: Naver에서 받은 state 값
        
    Returns:
        bool: 검증 성공 여부
    """
    saved_state = request.session.get('naver_oauth_state')
    if not saved_state or saved_state != state:
        return False
    
    # 사용 후 삭제 (일회용)
    del request.session['naver_oauth_state']
    return True
