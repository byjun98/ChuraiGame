"""
Django Management Command: Update Existing Games Sale Prices
==============================================================
DB에 이미 있는 게임들을 기반으로 세일 데이터셋을 생성/업데이트합니다.
CheapShark API에서 새 게임을 가져오지 않고, DB에 있는 게임들의 세일 정보만 수집합니다.

Usage:
    python manage.py update_existing_sales
    python manage.py update_existing_sales --limit 500
"""

import requests
import json
import time
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from games.models import Game


class Command(BaseCommand):
    help = 'Create sale dataset from games in DB (no new games from API)'

    CHEAPSHARK_API = "https://www.cheapshark.com/api/1.0"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of games to process (0 = all)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Print progress every N games'
        )

    def get_sale_price_by_steam_id(self, steam_appid):
        """Steam AppID로 CheapShark에서 현재 세일 가격 조회"""
        try:
            # CheapShark의 games API로 Steam AppID 검색
            response = requests.get(
                f"{self.CHEAPSHARK_API}/games",
                params={"steamAppID": str(steam_appid)},
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data or len(data) == 0:
                return None
            
            game_info = data[0]
            cheapest = game_info.get('cheapest', '0')
            cheapshark_id = game_info.get('gameID')
            
            # 상세 정보 조회로 현재 세일 가격 가져오기
            if cheapshark_id:
                time.sleep(0.5)  # 상세 조회 전 딜레이
                detail_response = requests.get(
                    f"{self.CHEAPSHARK_API}/games",
                    params={"id": cheapshark_id},
                    timeout=10
                )
                
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    deals = detail.get('deals', [])
                    
                    # Steam 스토어 (storeID = 1) 찾기
                    for deal in deals:
                        if deal.get('storeID') == '1':
                            sale_price = float(deal.get('price', 0))
                            retail_price = float(deal.get('retailPrice', 0))
                            savings = float(deal.get('savings', 0))
                            
                            return {
                                'cheapshark_id': cheapshark_id,
                                'current_price_usd': sale_price,
                                'original_price_usd': retail_price,
                                'current_price': int(sale_price * 1300),
                                'original_price': int(retail_price * 1300),
                                'discount_rate': round(savings / 100, 2) if savings else 0,
                                'deal_id': deal.get('dealID', ''),
                                'is_on_sale': savings > 0
                            }
                    
                    # Steam 스토어가 없으면 첫 번째 딜 사용
                    if deals:
                        deal = deals[0]
                        sale_price = float(deal.get('price', 0))
                        retail_price = float(deal.get('retailPrice', 0))
                        savings = float(deal.get('savings', 0))
                        
                        return {
                            'cheapshark_id': cheapshark_id,
                            'current_price_usd': sale_price,
                            'original_price_usd': retail_price,
                            'current_price': int(sale_price * 1300),
                            'original_price': int(retail_price * 1300),
                            'discount_rate': round(savings / 100, 2) if savings else 0,
                            'deal_id': deal.get('dealID', ''),
                            'is_on_sale': savings > 0
                        }
            
            return None
            
        except Exception as e:
            return None

    def handle(self, *args, **options):
        limit = options['limit']
        batch_size = options['batch_size']
        
        self.stdout.write(self.style.NOTICE(
            "� DB 게임 기반 세일 데이터셋 생성 시작"
        ))
        
        # 1. DB에서 Steam AppID가 있는 게임 가져오기
        db_games = Game.objects.filter(
            steam_appid__isnull=False
        ).exclude(
            steam_appid=0
        ).values('id', 'title', 'steam_appid', 'rawg_id', 'image_url', 'genre', 'metacritic_score')
        
        if limit > 0:
            db_games = db_games[:limit]
        
        total_games = len(db_games)
        self.stdout.write(f"   📊 DB 게임 수: {total_games}개")
        
        # 2. 각 게임의 세일 정보 조회
        sale_data = []
        on_sale_count = 0
        
        self.stdout.write(f"\n📊 CheapShark API로 세일 정보 조회 중...")
        
        for i, game in enumerate(db_games):
            steam_appid = game['steam_appid']
            
            # API 조회
            price_info = self.get_sale_price_by_steam_id(steam_appid)
            
            if price_info:
                # 세일 데이터 구성
                game_sale_info = {
                    'game_id': f"app{steam_appid}",
                    'steam_app_id': steam_appid,
                    'cheapshark_id': price_info.get('cheapshark_id'),
                    'deal_id': price_info.get('deal_id', ''),
                    'title': game['title'],
                    'current_price': price_info['current_price'],
                    'original_price': price_info['original_price'],
                    'current_price_usd': price_info['current_price_usd'],
                    'original_price_usd': price_info['original_price_usd'],
                    'discount_rate': price_info['discount_rate'],
                    'is_on_sale': price_info['is_on_sale'],
                    'rawg_id': game['rawg_id'],
                    'thumbnail': game['image_url'],
                    'image_url': game['image_url'],
                    'genre': game['genre'],
                    'metacritic_score': game['metacritic_score'] or 0,
                    'store_link': f"https://store.steampowered.com/app/{steam_appid}/",
                }
                
                sale_data.append(game_sale_info)
                
                if price_info['is_on_sale']:
                    on_sale_count += 1
            
            # 진행 상황 출력
            if (i + 1) % batch_size == 0:
                self.stdout.write(f"   ✅ {i + 1}/{total_games} 처리 완료 (세일 중: {on_sale_count})")
            
            # API 속도 제한 (CheapShark: 초당 1회 권장, 게임당 2번 호출하므로 1.5초)
            time.sleep(1.5)
        
        self.stdout.write(f"\n   📊 총 조회: {len(sale_data)}개, 세일 중: {on_sale_count}개")
        
        # 3. 데이터 정렬 및 분류
        # 할인율 순으로 정렬
        sale_data.sort(key=lambda x: x.get('discount_rate', 0), reverse=True)
        
        categorized = self._categorize_data(sale_data)
        
        # 4. 결과 저장
        result = {
            'updated_at': datetime.now().isoformat(),
            'source': 'CheapShark API (DB-based)',
            'stats': {
                'total_db_games': total_games,
                'total_with_price': len(sale_data),
                'on_sale_count': on_sale_count,
            },
            **categorized
        }
        
        structured_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_data.json')
        legacy_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
        
        try:
            with open(structured_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            with open(legacy_path, 'w', encoding='utf-8') as f:
                json.dump(sale_data, f, ensure_ascii=False, indent=2)
            
            self.stdout.write(self.style.SUCCESS(f"\n🎉 완료!"))
            self.stdout.write(f"   📊 DB 게임: {total_games}개")
            self.stdout.write(f"   � 가격 정보 있음: {len(sale_data)}개")
            self.stdout.write(f"   🔥 현재 세일 중: {on_sale_count}개")
            self.stdout.write(f"   📁 저장: {legacy_path}")
            
        except IOError as e:
            raise CommandError(f"파일 저장 실패: {e}")

    def _categorize_data(self, collected_data):
        """수집된 데이터를 카테고리별로 분류"""
        
        # 세일 중인 게임만 필터
        on_sale = [g for g in collected_data if g.get('is_on_sale', False)]
        
        current_sales = sorted(
            on_sale,
            key=lambda x: x.get('discount_rate', 0),
            reverse=True
        )
        
        popular_sales = sorted(
            [g for g in on_sale if g.get('discount_rate', 0) >= 0.3],
            key=lambda x: x.get('metacritic_score', 0),
            reverse=True
        )[:50]
        
        top_discounts = sorted(
            on_sale,
            key=lambda x: x.get('discount_rate', 0),
            reverse=True
        )[:50]
        
        highly_rated = sorted(
            [g for g in on_sale if g.get('metacritic_score', 0) >= 80],
            key=lambda x: x.get('metacritic_score', 0),
            reverse=True
        )[:50]
        
        return {
            'current_sales': current_sales[:500],
            'top_sales': popular_sales,
            'popular_sales': popular_sales,
            'top_discounts': top_discounts,
            'highly_rated': highly_rated,
            'best_prices': current_sales[:200]
        }
