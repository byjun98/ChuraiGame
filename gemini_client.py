"""
Gemini API Client - 무료 요금제 대응 (Rate Limiting)
=====================================================
Google Gemini API를 직접 호출하며, 무료 요금제의 분당 15 요청 제한에 맞춰
최소 4초 간격으로 요청을 보냅니다.

사용법:
    from gemini_client import gemini_generate, gemini_generate_with_image

환경변수:
    GEMINI_API_KEY: Google AI Studio에서 발급받은 API 키
"""

import os
import time
import threading
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ===========================================================================
# Rate Limiter (4초 간격 = 분당 최대 15요청, 무료 요금제 대응)
# ===========================================================================
_lock = threading.Lock()
_last_request_time = 0.0
RATE_LIMIT_SECONDS = 4.0  # 4초 간격

def _wait_for_rate_limit():
    """Rate limit 대기. 마지막 요청 후 4초가 안 지났으면 대기."""
    global _last_request_time
    with _lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < RATE_LIMIT_SECONDS:
            wait_time = RATE_LIMIT_SECONDS - elapsed
            logger.info(f"[Gemini Rate Limit] {wait_time:.1f}초 대기 중...")
            time.sleep(wait_time)
        _last_request_time = time.time()


# ===========================================================================
# API Configuration
# ===========================================================================
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-2.0-flash-lite"


def get_api_key():
    """API 키를 가져옵니다. 환경변수가 변경될 수 있으므로 매번 확인."""
    key = os.getenv('GEMINI_API_KEY', '') or GEMINI_API_KEY
    if not key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    return key


# ===========================================================================
# Core API Functions
# ===========================================================================

def gemini_generate(contents, system_instruction=None, generation_config=None, 
                    model=None, timeout=30):
    """
    Gemini API generateContent 호출 (텍스트 생성용)
    
    Args:
        contents: Gemini API contents 형식 
            예: [{"role": "user", "parts": [{"text": "안녕"}]}]
        system_instruction: 시스템 프롬프트 (선택)
            예: {"parts": [{"text": "당신은 게임 추천 AI입니다."}]}
        generation_config: 생성 설정 (선택)
            예: {"temperature": 0.7, "maxOutputTokens": 2048}
        model: 모델명 (기본: gemini-2.0-flash-lite)
        timeout: 요청 타임아웃 (초)
    
    Returns:
        dict: Gemini API 응답 JSON 전체
    
    Raises:
        requests.exceptions.RequestException: API 호출 실패
        ValueError: API 키 미설정
    """
    api_key = get_api_key()
    model_name = model or DEFAULT_MODEL
    url = f"{GEMINI_BASE_URL}/models/{model_name}:generateContent"
    
    payload = {
        "contents": contents,
    }
    
    if system_instruction:
        payload["systemInstruction"] = system_instruction
    
    if generation_config:
        payload["generationConfig"] = generation_config
    
    headers = {
        "Content-Type": "application/json"
    }
    
    params = {
        "key": api_key
    }
    
    # Rate limit 대기
    _wait_for_rate_limit()
    
    logger.info(f"[Gemini] 요청: model={model_name}")
    
    response = requests.post(
        url,
        params=params,
        headers=headers,
        json=payload,
        timeout=timeout
    )
    
    logger.info(f"[Gemini] 응답: status={response.status_code}")
    
    return response


def gemini_generate_with_image(contents, generation_config=None, 
                                model="gemini-2.0-flash-exp-image-generation", 
                                timeout=60):
    """
    Gemini 이미지 생성 API 호출
    
    Args:
        contents: Gemini API contents (텍스트 + inlineData 포함 가능)
        generation_config: 생성 설정
        model: 이미지 생성 모델명 (기본: gemini-2.0-flash-exp-image-generation)
        timeout: 요청 타임아웃 (초, 이미지 생성은 더 오래 걸림)
    
    Returns:
        dict: Gemini API 응답 JSON 전체
    """
    api_key = get_api_key()
    url = f"{GEMINI_BASE_URL}/models/{model}:generateContent"
    
    payload = {
        "contents": contents,
    }
    
    if generation_config:
        payload["generationConfig"] = generation_config
    
    headers = {
        "Content-Type": "application/json"
    }
    
    params = {
        "key": api_key
    }
    
    # Rate limit 대기
    _wait_for_rate_limit()
    
    logger.info(f"[Gemini Image] 요청: model={model}")
    
    response = requests.post(
        url,
        params=params,
        headers=headers,
        json=payload,
        timeout=timeout
    )
    
    logger.info(f"[Gemini Image] 응답: status={response.status_code}")
    
    return response


def extract_text(response_json):
    """
    Gemini 응답에서 텍스트를 추출합니다.
    
    Args:
        response_json: Gemini API 응답 JSON (response.json())
    
    Returns:
        str or None: 추출된 텍스트, 없으면 None
    """
    try:
        candidates = response_json.get('candidates', [])
        if candidates and candidates[0].get('content'):
            parts = candidates[0]['content'].get('parts', [])
            if parts:
                return parts[0].get('text', '')
    except (KeyError, IndexError) as e:
        logger.error(f"[Gemini] 텍스트 추출 실패: {e}")
    return None


def extract_image(response_json):
    """
    Gemini 이미지 응답에서 이미지 데이터를 추출합니다.
    
    Args:
        response_json: Gemini API 응답 JSON
    
    Returns:
        tuple: (image_base64, text_response) - 이미지와 텍스트 응답
    """
    image_base64 = None
    text_response = None
    
    try:
        candidates = response_json.get('candidates', [])
        if candidates:
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            
            for part in parts:
                if 'inlineData' in part:
                    image_base64 = part['inlineData'].get('data')
                if 'text' in part:
                    text_response = part['text']
    except (KeyError, IndexError) as e:
        logger.error(f"[Gemini Image] 이미지 추출 실패: {e}")
    
    return image_base64, text_response
