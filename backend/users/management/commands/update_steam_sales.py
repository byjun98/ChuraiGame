"""
Django Management Command: Update Steam Sales Data (CheapShark API)
=====================================================================
CheapShark API를 사용하여 양질의 스팀 세일 데이터를 가져옵니다.

주요 특징:
- 무료 API, API 키 불필요
- steamRatingCount >= 500 필터로 스캠 게임 원천 차단
- steamRating >= 75 필터로 좋은 평가의 게임만 수집
- 역대 최저가 정보 포함

Usage:
    python manage.py update_steam_sales
    python manage.py update_steam_sales --count 300
    python manage.py update_steam_sales --min-reviews 1000
"""

import requests
import json
import time
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Fetch and update Steam sale data using CheapShark API (high-quality games only)'

    # CheapShark API Endpoints
    DEALS_API_URL = "https://www.cheapshark.com/api/1.0/deals"
    GAMES_API_URL = "https://www.cheapshark.com/api/1.0/games"
    PAGE_SIZE = 60  # CheapShark 최대값

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=500,
            help='Number of sale items to fetch (default: 500)'
        )
        parser.add_argument(
            '--min-rating',
            type=int,
            default=75,
            help='Minimum Steam rating percentage (default: 75)'
        )
        parser.add_argument(
            '--min-reviews',
            type=int,
            default=500,
            help='Minimum review count to filter scam games (default: 500)'
        )
        parser.add_argument(
            '--fetch-history',
            action='store_true',
            default=True,
            help='Fetch historical low prices for top games (default: True)'
        )
        parser.add_argument(
            '--no-history',
            action='store_true',
            help='Skip fetching historical low prices'
        )

    def fetch_deals(self, page_number=0, min_rating=75):
        """CheapShark Deals API로 세일 게임 목록 조회"""
        params = {
            "storeID": "1",          # 1 = Steam
            "onSale": "1",           # 현재 세일 중
            "steamRating": str(min_rating),
            "pageSize": str(self.PAGE_SIZE),
            "pageNumber": str(page_number),
            "sortBy": "Deal Rating"
        }
        
        try:
            response = requests.get(self.DEALS_API_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f"❌ API 요청 실패: {e}"))
            return []

    def fetch_historical_low(self, game_id):
        """CheapShark Games API로 역대 최저가 정보 조회"""
        try:
            response = requests.get(f"{self.GAMES_API_URL}?id={game_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('cheapestPriceEver', None)
        except Exception:
            pass
        return None

    def handle(self, *args, **options):
        target_count = options['count']
        min_rating = options['min_rating']
        min_reviews = options['min_reviews']
        fetch_history = not options['no_history']
        
        self.stdout.write(self.style.NOTICE(
            f"🚀 CheapShark API로 Steam 세일 데이터 업데이트 시작"
        ))
        self.stdout.write(f"   목표: {target_count}개")
        self.stdout.write(f"   필터: 스팀 평가 {min_rating}% 이상, 리뷰 {min_reviews}개 이상")
        self.stdout.write("")
        
        collected_data = []
        page = 0
        
        # 데이터 수집
        while len(collected_data) < target_count:
            deals = self.fetch_deals(page_number=page, min_rating=min_rating)
            
            if not deals:
                self.stdout.write(self.style.WARNING("🏁 더 이상 데이터가 없습니다."))
                break
            
            filtered_count = 0
            for deal in deals:
                # 리뷰 개수 필터링 (핵심! 스캠 게임 차단)
                review_count = int(deal.get('steamRatingCount') or 0)
                if review_count < min_reviews:
                    filtered_count += 1
                    continue
                
                # 스팀 앱 ID가 없는 경우 스킵
                steam_app_id = deal.get('steamAppID')
                if not steam_app_id:
                    continue
                
                # 할인율 계산
                savings = float(deal.get('savings') or 0)
                discount_rate = round(savings / 100, 2)
                
                # 가격 변환 (달러 -> 원화)
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
                    'is_on_sale': deal.get('isOnSale') == "1",
                    'sale_count': review_count  # 하위 호환성을 위해 리뷰 수를 sale_count로도 저장
                }
                
                collected_data.append(game_info)
            
            if page % 3 == 0:
                self.stdout.write(f"   ✅ 페이지 {page + 1} 완료 (수집: {len(collected_data)}개)")
            
            page += 1
            time.sleep(0.3)
            
            if page > 50:
                self.stdout.write(self.style.WARNING("⚠️ 최대 페이지 도달"))
                break
        
        # 목표 개수에 맞춰 자르기
        collected_data = collected_data[:target_count]
        
        # 역대 최저가 정보 조회
        if fetch_history and len(collected_data) > 0:
            self.stdout.write(f"\n📊 역대 최저가 정보 조회 중... (상위 100개)")
            for i, game in enumerate(collected_data[:100]):
                cheapshark_id = game.get('cheapshark_id')
                if cheapshark_id:
                    historical = self.fetch_historical_low(cheapshark_id)
                    if historical:
                        game['cheapest_price_ever'] = float(historical.get('price', 0))
                        game['cheapest_price_ever_krw'] = int(float(historical.get('price', 0)) * 1300)
                        game['cheapest_date'] = historical.get('date', '')
                        
                        if game['current_price_usd'] <= float(historical.get('price', 999)):
                            game['is_historical_low'] = True
                        else:
                            game['is_historical_low'] = False
                
                if (i + 1) % 20 == 0:
                    self.stdout.write(f"   ✅ {i + 1}/100 완료")
                time.sleep(0.2)
        
        # 데이터 분류
        categorized = self._categorize_data(collected_data)
        
        # 결과 저장
        result = {
            'updated_at': datetime.now().isoformat(),
            'source': 'CheapShark API',
            'filters': {
                'min_steam_rating': min_rating,
                'min_review_count': min_reviews
            },
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
            self.stdout.write(f"   📊 전체 수집: {len(collected_data)}개")
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
        
        # 하위 호환성: top_sales와 best_prices도 포함
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
