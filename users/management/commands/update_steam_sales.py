"""
Django Management Command: Update Steam Sales Data (CheapShark API)
=====================================================================
CheapShark API를 사용하여 DB에 있는 게임들의 스팀 세일 데이터를 가져옵니다.

주요 특징:
- DB에 있는 게임들만 수집 (새 게임 추가 없음)
- 무료 API, API 키 불필요
- Rate limiting 방지를 위한 적절한 딜레이
- 역대 최저가 정보 포함

Usage:
    python manage.py update_steam_sales
    python manage.py update_steam_sales --no-history
"""

import requests
import json
import time
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Fetch and update Steam sale data for games already in DB using CheapShark API'

    # CheapShark API Endpoints
    DEALS_API_URL = "https://www.cheapshark.com/api/1.0/deals"
    GAMES_API_URL = "https://www.cheapshark.com/api/1.0/games"
    PAGE_SIZE = 60  # CheapShark 최대값
    
    # Rate limiting 방지
    REQUEST_DELAY = 1.0  # 1초 딜레이 (안전하게)
    HISTORY_DELAY = 0.5  # 역대 최저가 조회는 더 빠르게

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-history',
            action='store_true',
            help='Skip fetching historical low prices'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay between API requests in seconds (default: 1.0)'
        )

    def fetch_deals_with_retry(self, params, max_retries=3):
        """CheapShark API 호출 (429 에러 시 Retry-After 대기)"""
        for attempt in range(max_retries):
            try:
                response = requests.get(self.DEALS_API_URL, params=params, timeout=30)
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.stdout.write(self.style.WARNING(
                        f"⏳ Rate limited! {retry_after}초 대기 후 재시도..."
                    ))
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    self.stdout.write(self.style.WARNING(f"⚠️ 요청 실패, 재시도 중... ({e})"))
                    time.sleep(5)
                else:
                    self.stdout.write(self.style.ERROR(f"❌ API 요청 실패: {e}"))
                    return []
        return []

    def fetch_historical_low_with_retry(self, game_id, max_retries=2):
        """CheapShark Games API로 역대 최저가 정보 조회 (429 처리 포함)"""
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.GAMES_API_URL}?id={game_id}", timeout=10)
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 30))
                    self.stdout.write(self.style.WARNING(f"⏳ Rate limited! {retry_after}초 대기..."))
                    time.sleep(retry_after)
                    continue
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('cheapestPriceEver', None)
            except Exception:
                pass
        return None

    def handle(self, *args, **options):
        fetch_history = not options['no_history']
        self.REQUEST_DELAY = options['delay']
        
        self.stdout.write(self.style.NOTICE(
            f"🚀 CheapShark API로 DB 게임들의 세일 데이터 업데이트 시작"
        ))
        self.stdout.write(f"   📌 모드: DB에 있는 게임만 수집 (새 게임 추가 안함)")
        self.stdout.write(f"   ⏱️ 요청 딜레이: {self.REQUEST_DELAY}초")
        self.stdout.write("")
        
        # DB에서 게임 정보 먼저 로드
        from games.models import Game
        
        db_steam_ids = set()
        steam_to_rawg = {}
        games_with_steam = Game.objects.filter(
            steam_appid__isnull=False
        ).exclude(steam_appid=0).values_list('steam_appid', 'rawg_id')
        
        for steam_appid, rawg_id in games_with_steam:
            db_steam_ids.add(str(steam_appid))
            if rawg_id:
                steam_to_rawg[str(steam_appid)] = rawg_id
        
        self.stdout.write(f"   📊 DB에 있는 Steam 게임: {len(db_steam_ids)}개")
        self.stdout.write("")
        
        # 중복 체크용 set
        seen_app_ids = set()
        collected_data = []
        
        def process_deals(deals):
            """딜 데이터를 처리하여 collected_data에 추가 (DB 게임만, 중복 제거)"""
            added = 0
            for deal in deals:
                steam_app_id = deal.get('steamAppID')
                if not steam_app_id:
                    continue
                
                # ★ DB에 있는 게임만 수집 ★
                if str(steam_app_id) not in db_steam_ids:
                    continue
                
                # 중복 체크
                if steam_app_id in seen_app_ids:
                    continue
                seen_app_ids.add(steam_app_id)
                
                # 할인율 계산
                savings = float(deal.get('savings') or 0)
                discount_rate = round(savings / 100, 2)
                
                # 가격 변환 (달러 -> 원화)
                sale_price_usd = float(deal.get('salePrice') or 0)
                normal_price_usd = float(deal.get('normalPrice') or 0)
                sale_price_krw = int(sale_price_usd * 1300)
                normal_price_krw = int(normal_price_usd * 1300)
                
                deal_id = deal.get('dealID', '')
                cheapshark_url = f"https://www.cheapshark.com/redirect?dealID={deal_id}" if deal_id else ""
                
                review_count = int(deal.get('steamRatingCount') or 0)
                
                game_info = {
                    'game_id': f"app{steam_app_id}",
                    'steam_app_id': steam_app_id,
                    'cheapshark_id': deal.get('gameID'),
                    'deal_id': deal_id,
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
                    'cheapshark_url': cheapshark_url,
                    'is_on_sale': deal.get('isOnSale') == "1",
                    'sale_count': review_count,
                    'rawg_id': steam_to_rawg.get(str(steam_app_id))  # 미리 매핑
                }
                
                collected_data.append(game_info)
                added += 1
            return added
        
        # CheapShark deals API를 페이지네이션으로 순회
        # 여러 정렬 기준으로 수집하여 다양한 게임 확보
        
        sort_criteria = [
            ("Deal Rating", 30),   # Deal Rating으로 30페이지
            ("Reviews", 30),       # 인기도로 30페이지
            ("Metacritic", 20),    # 메타크리틱으로 20페이지
            ("Savings", 20),       # 할인율로 20페이지
        ]
        
        for sort_by, max_pages in sort_criteria:
            self.stdout.write(f"📥 {sort_by} 기준 수집 중...")
            
            for page in range(max_pages):
                params = {
                    "storeID": "1",
                    "onSale": "1",
                    "pageSize": str(self.PAGE_SIZE),
                    "pageNumber": str(page),
                    "sortBy": sort_by
                }
                
                deals = self.fetch_deals_with_retry(params)
                
                if not deals:
                    self.stdout.write(f"   ⚠️ 페이지 {page + 1}에서 데이터 없음, 다음으로 넘어감")
                    break
                
                added = process_deals(deals)
                
                if (page + 1) % 10 == 0:
                    self.stdout.write(f"   ✅ 페이지 {page + 1}/{max_pages} (수집: {len(collected_data)}개, +{added} 신규)")
                
                time.sleep(self.REQUEST_DELAY)
            
            self.stdout.write(f"   ✅ {sort_by}: 완료 (누적: {len(collected_data)}개)")
        
        self.stdout.write(f"\n📊 1차 수집 완료: {len(collected_data)}개 (DB 게임 중 세일 중인 것)")
        
        # 역대 최저가 정보 조회
        if fetch_history and len(collected_data) > 0:
            history_count = min(len(collected_data), 300)  # 최대 300개만
            self.stdout.write(f"\n📊 역대 최저가 정보 조회 중... (상위 {history_count}개)")
            
            for i, game in enumerate(collected_data[:history_count]):
                cheapshark_id = game.get('cheapshark_id')
                if cheapshark_id:
                    historical = self.fetch_historical_low_with_retry(cheapshark_id)
                    if historical:
                        game['cheapest_price_ever'] = float(historical.get('price', 0))
                        game['cheapest_price_ever_krw'] = int(float(historical.get('price', 0)) * 1300)
                        game['cheapest_date'] = historical.get('date', '')
                        
                        if game['current_price_usd'] <= float(historical.get('price', 999)):
                            game['is_historical_low'] = True
                        else:
                            game['is_historical_low'] = False
                
                if (i + 1) % 50 == 0:
                    self.stdout.write(f"   ✅ {i + 1}/{history_count} 완료")
                
                time.sleep(self.HISTORY_DELAY)
        
        # 데이터 분류
        categorized = self._categorize_data(collected_data)
        
        # 결과 저장
        result = {
            'updated_at': datetime.now().isoformat(),
            'source': 'CheapShark API (DB games only)',
            'db_game_count': len(db_steam_ids),
            'stats': {
                'total_count': len(collected_data),
                'popular_count': len(categorized['popular_sales']),
                'top_discount_count': len(categorized['top_discounts']),
                'historical_low_count': len(categorized.get('historical_lows', [])),
                'highly_rated_count': len(categorized['highly_rated'])
            },
            **categorized
        }
        
        # 파일 저장
        structured_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_data.json')
        legacy_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
        
        try:
            with open(structured_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            with open(legacy_path, 'w', encoding='utf-8') as f:
                json.dump(collected_data, f, ensure_ascii=False, indent=2)
            
            self.stdout.write(self.style.SUCCESS("\n🎉 완료!"))
            self.stdout.write(f"   📊 DB 게임 총: {len(db_steam_ids)}개")
            self.stdout.write(f"   📊 세일 중인 게임: {len(collected_data)}개")
            self.stdout.write(f"   🔥 인기 세일: {len(categorized['popular_sales'])}개")
            self.stdout.write(f"   💰 역대 최대 할인: {len(categorized['top_discounts'])}개")
            self.stdout.write(f"   ⭐ 역대 최저가: {len(categorized.get('historical_lows', []))}개")
            self.stdout.write(f"   🌟 높은 평가: {len(categorized['highly_rated'])}개")
            self.stdout.write(f"   📁 저장 위치: {structured_path}")
            self.stdout.write(f"   📁 레거시 파일: {legacy_path}")
            
        except IOError as e:
            raise CommandError(f"파일 저장 실패: {e}")

    def _categorize_data(self, collected_data):
        """수집된 데이터를 카테고리별로 분류"""
        
        # 1. 현재 세일 중 (전체)
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
        
        # 3. 역대 최대 할인 (평가 좋은 것 중)
        top_discounts = sorted(
            [g for g in collected_data if g.get('steam_rating', 0) >= 85],
            key=lambda x: x.get('discount_rate', 0),
            reverse=True
        )[:50]
        
        # 4. 역대 최저가
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
        
        # 하위 호환성
        top_sales = popular_sales
        best_prices = [
            {**g, 'is_best_price': g.get('is_historical_low', False)}
            for g in current_sales[:200]
        ]
        
        return {
            'current_sales': current_sales[:500],
            'top_sales': top_sales,
            'popular_sales': popular_sales,
            'top_discounts': top_discounts,
            'historical_lows': historical_lows,
            'highly_rated': highly_rated,
            'best_prices': best_prices
        }
