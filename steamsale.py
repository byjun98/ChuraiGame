"""
Steam Sale Data Fetcher using CheapShark API
============================================
CheapShark API를 사용하여 양질의 스팀 세일 데이터를 수집합니다.

주요 특징:
- 무료 API, API 키 불필요
- steamRatingCount >= 500 필터로 스캠 게임 원천 차단
- steamRating >= 80 필터로 좋은 평가의 게임만 수집
- 역대 최저가 정보 포함

Usage:
    python steamsale.py
"""

import requests
import json
import time
from datetime import datetime

# ==========================================
# 설정
# ==========================================
TARGET_COUNT = 500          # 목표 수집 개수
PAGE_SIZE = 60              # 한 번에 가져올 개수 (CheapShark 최대 60)
MIN_STEAM_RATING = 75       # 최소 스팀 평가 점수 (%)
MIN_REVIEW_COUNT = 500      # 최소 리뷰 개수 (스캠 필터링 핵심!)
FETCH_HISTORICAL_LOW = True # 역대 최저가 정보 조회 여부

# CheapShark API Endpoints
DEALS_API_URL = "https://www.cheapshark.com/api/1.0/deals"
GAMES_API_URL = "https://www.cheapshark.com/api/1.0/games"


def fetch_deals(page_number=0, sort_by="Deal Rating"):
    """
    CheapShark Deals API로 세일 게임 목록 조회
    
    Args:
        page_number: 페이지 번호 (0부터 시작)
        sort_by: 정렬 기준 ("Deal Rating", "Title", "Savings", "Price", "Metacritic", "Reviews", "Release", "Store", "recent")
    
    Returns:
        list: 세일 게임 정보 목록
    """
    params = {
        "storeID": "1",                     # 1 = Steam
        "onSale": "1",                       # 현재 세일 중인 것만
        "steamRating": str(MIN_STEAM_RATING), # 스팀 평가 75% 이상
        "pageSize": str(PAGE_SIZE),
        "pageNumber": str(page_number),
        "sortBy": sort_by
    }
    
    try:
        response = requests.get(DEALS_API_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API 요청 실패: {e}")
        return []


def fetch_historical_low(game_id):
    """
    CheapShark Games API로 역대 최저가 정보 조회
    
    Args:
        game_id: CheapShark 게임 ID
    
    Returns:
        dict: cheapestPriceEver 정보 또는 None
    """
    try:
        response = requests.get(f"{GAMES_API_URL}?id={game_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('cheapestPriceEver', None)
    except Exception:
        pass
    return None


def crawl_steam_sales():
    """
    CheapShark API를 사용하여 양질의 스팀 세일 데이터 수집
    """
    collected_data = []
    page = 0
    
    print(f"🚀 CheapShark API 크롤링 시작")
    print(f"   목표: {TARGET_COUNT}개")
    print(f"   필터: 스팀 평가 {MIN_STEAM_RATING}% 이상, 리뷰 {MIN_REVIEW_COUNT}개 이상")
    print()
    
    while len(collected_data) < TARGET_COUNT:
        deals = fetch_deals(page_number=page)
        
        if not deals:
            print("🏁 더 이상 데이터가 없습니다.")
            break
        
        filtered_count = 0
        for deal in deals:
            # 리뷰 개수 필터링 (핵심! 스캠 게임 차단)
            review_count = int(deal.get('steamRatingCount') or 0)
            if review_count < MIN_REVIEW_COUNT:
                filtered_count += 1
                continue
            
            # 스팀 앱 ID가 없는 경우 스킵
            steam_app_id = deal.get('steamAppID')
            if not steam_app_id:
                continue
            
            # 할인율 계산 (savings는 문자열로 옴, 예: "90.045023")
            savings = float(deal.get('savings') or 0)
            discount_rate = round(savings / 100, 2)  # 0.90 형태로 변환
            
            # 가격 변환 (달러 -> 원화 근사치, $1 = ₩1,300)
            sale_price_usd = float(deal.get('salePrice') or 0)
            normal_price_usd = float(deal.get('normalPrice') or 0)
            sale_price_krw = int(sale_price_usd * 1300)
            normal_price_krw = int(normal_price_usd * 1300)
            
            # CheapShark redirect URL 생성 (다른 스토어로 연결 가능)
            deal_id = deal.get('dealID', '')
            cheapshark_url = f"https://www.cheapshark.com/redirect?dealID={deal_id}" if deal_id else ""
            
            game_info = {
                'game_id': f"app{steam_app_id}",
                'steam_app_id': steam_app_id,
                'cheapshark_id': deal.get('gameID'),
                'deal_id': deal_id,  # CheapShark deal ID
                'title': deal.get('title'),
                'current_price': sale_price_krw,
                'original_price': normal_price_krw,
                'current_price_usd': sale_price_usd,
                'original_price_usd': normal_price_usd,
                'discount_rate': discount_rate,
                'steam_rating': int(deal.get('steamRatingPercent') or 0),
                'steam_rating_text': deal.get('steamRatingText', ''),
                'review_count': review_count,
                'metacritic_score': int(deal.get('metacriticScore') or 0),
                'deal_rating': deal.get('dealRating', '0'),
                'thumbnail': deal.get('thumb'),
                'store_link': f"https://store.steampowered.com/app/{steam_app_id}/",
                'cheapshark_url': cheapshark_url,  # 가격 비교 / 다른 스토어 링크
                'is_on_sale': deal.get('isOnSale') == "1"
            }
            
            collected_data.append(game_info)
        
        print(f"   ✅ 페이지 {page + 1} 완료 (수집: {len(collected_data)}개, 필터링됨: {filtered_count}개)")
        
        page += 1
        time.sleep(0.3)  # API 예의
        
        # 무한 루프 방지
        if page > 50:
            print("⚠️ 최대 페이지 도달")
            break
    
    # 목표 개수에 맞춰 자르기
    collected_data = collected_data[:TARGET_COUNT]
    
    # 역대 최저가 정보 조회 (선택적)
    if FETCH_HISTORICAL_LOW and len(collected_data) > 0:
        print(f"\n📊 역대 최저가 정보 조회 중... (상위 100개)")
        for i, game in enumerate(collected_data[:100]):
            cheapshark_id = game.get('cheapshark_id')
            if cheapshark_id:
                historical = fetch_historical_low(cheapshark_id)
                if historical:
                    game['cheapest_price_ever'] = float(historical.get('price', 0))
                    game['cheapest_price_ever_krw'] = int(float(historical.get('price', 0)) * 1300)
                    game['cheapest_date'] = historical.get('date', '')
                    
                    # 현재 가격이 역대 최저가인지 확인
                    if game['current_price_usd'] <= float(historical.get('price', 999)):
                        game['is_historical_low'] = True
                    else:
                        game['is_historical_low'] = False
            
            if (i + 1) % 10 == 0:
                print(f"   ✅ {i + 1}/100 완료")
            time.sleep(0.2)  # API 예의
    
    return collected_data


def categorize_data(collected_data):
    """
    수집된 데이터를 카테고리별로 분류
    """
    # 1. 현재 세일 중 (전체 목록)
    current_sales = sorted(
        collected_data, 
        key=lambda x: x.get('discount_rate', 0), 
        reverse=True
    )
    
    # 2. 인기 게임 세일 (리뷰 많은 순)
    popular_sales = sorted(
        [g for g in collected_data if g.get('discount_rate', 0) >= 0.3],
        key=lambda x: x.get('review_count', 0),
        reverse=True
    )[:50]
    
    # 3. 역대 최대 할인 (할인율 높은 순, 평가 좋은 것만)
    top_discounts = sorted(
        [g for g in collected_data if g.get('steam_rating', 0) >= 85],
        key=lambda x: x.get('discount_rate', 0),
        reverse=True
    )[:50]
    
    # 4. 역대 최저가 게임
    historical_lows = [
        g for g in collected_data 
        if g.get('is_historical_low', False)
    ][:30]
    
    # 5. 높은 평가 게임
    highly_rated = sorted(
        [g for g in collected_data if g.get('steam_rating', 0) >= 90],
        key=lambda x: (x.get('steam_rating', 0), x.get('review_count', 0)),
        reverse=True
    )[:50]
    
    return {
        'current_sales': current_sales,
        'popular_sales': popular_sales,
        'top_discounts': top_discounts,
        'historical_lows': historical_lows,
        'highly_rated': highly_rated
    }


def save_data(categorized_data, collected_data):
    """
    데이터를 JSON 파일로 저장
    """
    # 구조화된 데이터 저장
    result = {
        'updated_at': datetime.now().isoformat(),
        'source': 'CheapShark API',
        'filters': {
            'min_steam_rating': MIN_STEAM_RATING,
            'min_review_count': MIN_REVIEW_COUNT
        },
        'stats': {
            'total_count': len(collected_data),
            'popular_count': len(categorized_data['popular_sales']),
            'top_discount_count': len(categorized_data['top_discounts']),
            'historical_low_count': len(categorized_data['historical_lows']),
            'highly_rated_count': len(categorized_data['highly_rated'])
        },
        **categorized_data
    }
    
    structured_path = 'users/steam_sale_data.json'
    with open(structured_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 레거시 형식 저장 (하위 호환성)
    legacy_path = 'users/steam_sale_dataset_fast.json'
    with open(legacy_path, 'w', encoding='utf-8') as f:
        json.dump(collected_data, f, ensure_ascii=False, indent=2)
    
    return structured_path, legacy_path


def main():
    """
    메인 실행 함수
    """
    print("=" * 60)
    print("🎮 Steam Sale Data Fetcher (CheapShark API)")
    print("=" * 60)
    print()
    
    # 데이터 수집
    collected_data = crawl_steam_sales()
    
    if not collected_data:
        print("❌ 수집된 데이터가 없습니다.")
        return
    
    # 데이터 분류
    print("\n📦 데이터 분류 중...")
    categorized_data = categorize_data(collected_data)
    
    # 저장
    structured_path, legacy_path = save_data(categorized_data, collected_data)
    
    # 결과 출력
    print()
    print("=" * 60)
    print("🎉 완료!")
    print("=" * 60)
    print(f"   📊 전체 수집: {len(collected_data)}개")
    print(f"   🔥 인기 세일: {len(categorized_data['popular_sales'])}개")
    print(f"   💰 역대 최대 할인: {len(categorized_data['top_discounts'])}개")
    print(f"   ⭐ 역대 최저가: {len(categorized_data['historical_lows'])}개")
    print(f"   🌟 높은 평가: {len(categorized_data['highly_rated'])}개")
    print()
    print(f"   📁 구조화된 데이터: {structured_path}")
    print(f"   📁 레거시 데이터: {legacy_path}")
    print()
    
    # 샘플 데이터 출력
    if collected_data:
        print("📋 샘플 데이터 (상위 5개):")
        for i, game in enumerate(collected_data[:5]):
            print(f"   {i + 1}. {game['title']}")
            print(f"      가격: ${game['current_price_usd']} (원래 ${game['original_price_usd']})")
            print(f"      할인율: {int(game['discount_rate'] * 100)}%")
            print(f"      스팀 평가: {game['steam_rating']}% ({game['review_count']:,}개 리뷰)")
            if game.get('is_historical_low'):
                print(f"      🔥 역대 최저가!")
            print()


# 실행
if __name__ == "__main__":
    while True:
        main()
        print("⏳ 24시간 대기 중...")
        time.sleep(86400)