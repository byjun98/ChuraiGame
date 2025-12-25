"""
DB에 있지만 세일 데이터셋에 없는 게임들의 가격 정보를 CheapShark API로 가져오는 스크립트

Usage:
    python manage.py shell < users/management/scripts/fetch_missing_prices.py
    
Or run as management command:
    python manage.py fetch_missing_prices
    python manage.py fetch_missing_prices --limit=100  # 최대 100개만
    python manage.py fetch_missing_prices --apply      # 데이터셋에 저장
"""

from django.core.management.base import BaseCommand
import json
import os
import time
import requests
from django.conf import settings
from games.models import Game


class Command(BaseCommand):
    help = 'DB에 있지만 세일 데이터셋에 없는 게임들의 CheapShark 가격 정보 가져오기'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=200,
            help='처리할 최대 게임 수 (default: 200)'
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='실제로 데이터셋에 저장'
        )
        parser.add_argument(
            '--steam-only',
            action='store_true',
            help='Steam AppID가 있는 게임만 처리'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        apply = options['apply']
        steam_only = options['steam_only']
        
        self.stdout.write("=" * 60)
        self.stdout.write("CheapShark 가격 정보 가져오기")
        self.stdout.write("=" * 60)
        
        # 1. 데이터셋 로드
        dataset_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        dataset_titles = set(g.get('title', '').lower().strip() for g in dataset)
        dataset_steam_ids = set(g.get('steam_app_id') for g in dataset if g.get('steam_app_id'))
        
        self.stdout.write(f"현재 데이터셋: {len(dataset)}개 게임")
        
        # 2. DB에만 있는 게임 찾기
        db_only_games = []
        
        for game in Game.objects.all():
            title_lower = game.title.lower().strip()
            
            # 이미 데이터셋에 있는지 확인 (제목 또는 Steam AppID)
            if title_lower in dataset_titles:
                continue
            if game.steam_appid and game.steam_appid in dataset_steam_ids:
                continue
            
            # Steam AppID 필터
            if steam_only and not game.steam_appid:
                continue
            
            db_only_games.append(game)
        
        self.stdout.write(f"DB에만 있는 게임: {len(db_only_games)}개")
        
        # Steam AppID가 있는 게임 우선
        db_only_games.sort(key=lambda g: (0 if g.steam_appid else 1, g.id))
        
        # 처리할 게임 선택
        games_to_process = db_only_games[:limit]
        self.stdout.write(f"처리할 게임: {len(games_to_process)}개")
        self.stdout.write("-" * 60)
        
        # 3. CheapShark API로 가격 정보 가져오기
        new_entries = []
        failed = []
        
        for i, game in enumerate(games_to_process):
            self.stdout.write(f"[{i+1}/{len(games_to_process)}] {game.title}...", ending='')
            
            price_info = self.fetch_cheapshark_price(game)
            
            if price_info:
                new_entries.append(price_info)
                self.stdout.write(self.style.SUCCESS(
                    f" ✓ ${price_info['current_price']/100:.2f} (할인 {price_info['discount_rate']*100:.0f}%)"
                ))
            else:
                failed.append(game.title)
                self.stdout.write(self.style.WARNING(" ✗ 가격 정보 없음"))
            
            # Rate limiting (CheapShark는 초당 1회 권장)
            time.sleep(1.0)
        
        self.stdout.write("-" * 60)
        self.stdout.write(f"성공: {len(new_entries)}개, 실패: {len(failed)}개")
        
        # 4. 데이터셋에 저장
        if apply and new_entries:
            # 기존 데이터셋에 추가
            dataset.extend(new_entries)
            
            # 저장
            with open(dataset_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            
            self.stdout.write(self.style.SUCCESS(f"✅ {len(new_entries)}개 게임이 데이터셋에 추가되었습니다!"))
            self.stdout.write(f"새 데이터셋 크기: {len(dataset)}개")
        elif new_entries:
            self.stdout.write(self.style.WARNING("⚠️ Dry-run 모드. 실제 저장하려면 --apply 옵션을 추가하세요."))
            
            # 미리보기
            self.stdout.write("\n추가될 게임 미리보기 (상위 10개):")
            for entry in new_entries[:10]:
                self.stdout.write(f"  - {entry['title']}: ₩{entry['current_price']:,} (할인 {entry['discount_rate']*100:.0f}%)")

    def fetch_cheapshark_price(self, game):
        """CheapShark API로 게임 가격 정보 가져오기"""
        
        # Steam AppID로 조회 (가장 정확)
        if game.steam_appid:
            try:
                # Steam AppID로 직접 조회
                response = requests.get(
                    f"https://www.cheapshark.com/api/1.0/games",
                    params={'steamAppID': game.steam_appid},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        game_data = data[0]
                        deals = game_data.get('deals', [])
                        
                        if deals:
                            # Steam 딜 찾기 (storeID=1이 Steam)
                            steam_deal = None
                            for deal in deals:
                                if deal.get('storeID') == '1':
                                    steam_deal = deal
                                    break
                            
                            if not steam_deal:
                                steam_deal = deals[0]  # Steam 없으면 첫 번째 딜
                            
                            return self.create_entry(game, game_data, steam_deal)
            except Exception as e:
                pass
        
        # 제목으로 검색 (fallback)
        try:
            response = requests.get(
                "https://www.cheapshark.com/api/1.0/games",
                params={'title': game.title, 'limit': 5},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # 제목이 비슷한 게임 찾기
                for result in data:
                    if self.titles_match(game.title, result.get('external', '')):
                        # 상세 정보 가져오기
                        game_id = result.get('gameID')
                        if game_id:
                            detail_resp = requests.get(
                                f"https://www.cheapshark.com/api/1.0/games",
                                params={'id': game_id},
                                timeout=10
                            )
                            if detail_resp.status_code == 200:
                                detail = detail_resp.json()
                                deals = detail.get('deals', [])
                                if deals:
                                    return self.create_entry(game, detail, deals[0])
        except Exception as e:
            pass
        
        return None

    def titles_match(self, title1, title2):
        """두 제목이 유사한지 확인"""
        import re
        
        def normalize(s):
            s = s.lower()
            s = re.sub(r'[^\w\s]', '', s)  # 특수문자 제거
            s = re.sub(r'\s+', ' ', s).strip()
            return s
        
        t1 = normalize(title1)
        t2 = normalize(title2)
        
        return t1 == t2 or t1 in t2 or t2 in t1

    def create_entry(self, game, cheapshark_data, deal):
        """세일 데이터셋 형식으로 엔트리 생성"""
        
        # 가격 파싱 (CheapShark는 달러 문자열 반환)
        try:
            current_price = float(deal.get('price', 0))
            retail_price = float(deal.get('retailPrice', current_price))
        except:
            current_price = 0
            retail_price = 0
        
        # 할인율 계산
        if retail_price > 0:
            discount_rate = (retail_price - current_price) / retail_price
        else:
            discount_rate = 0
        
        # 원화 변환 (대략적)
        usd_to_krw = 1350
        current_price_krw = int(current_price * usd_to_krw)
        original_price_krw = int(retail_price * usd_to_krw)
        
        # 썸네일 URL
        thumbnail = f"https://cdn.akamai.steamstatic.com/steam/apps/{game.steam_appid}/header.jpg" if game.steam_appid else game.image_url
        
        return {
            'title': game.title,
            'game_id': f"app{game.steam_appid}" if game.steam_appid else str(game.id),
            'steam_app_id': game.steam_appid,
            'rawg_id': game.rawg_id,
            'discount_rate': round(discount_rate, 2),
            'current_price': current_price_krw,
            'original_price': original_price_krw,
            'thumbnail': thumbnail,
            'store_link': f"https://store.steampowered.com/app/{game.steam_appid}/" if game.steam_appid else '',
            'cheapshark_id': cheapshark_data.get('gameID', ''),
            'cheapshark_url': f"https://www.cheapshark.com/redirect?dealID={deal.get('dealID', '')}" if deal.get('dealID') else '',
            'steam_rating': 0,  # CheapShark에서는 스팀 평점을 제공하지 않음
            'review_count': 0,
            'metacritic_score': cheapshark_data.get('info', {}).get('metacriticScore') or game.metacritic_score or 0,
            'is_historical_low': deal.get('price', '') == cheapshark_data.get('info', {}).get('cheapestPriceEver', {}).get('price', ''),
            'source': 'cheapshark_fetch',
        }
