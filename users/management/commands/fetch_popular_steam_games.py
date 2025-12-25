"""
Django Management Command: Fetch Popular Steam Games
=====================================================
Steam에서 직접 인기 게임을 가져와 DB에 추가합니다.
CheapShark과 달리 세일 여부와 상관없이 인기 게임을 수집합니다.

데이터 소스:
- SteamSpy API (인기 게임 목록)
- Steam Store API (게임 상세 정보)

Usage:
    python manage.py fetch_popular_steam_games
    python manage.py fetch_popular_steam_games --count 1000
    python manage.py fetch_popular_steam_games --top-rated
"""

import requests
import time
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Fetch popular Steam games directly from Steam/SteamSpy API'

    # SteamSpy API
    STEAMSPY_TOP_URL = "https://steamspy.com/api.php?request=top100in2weeks"
    STEAMSPY_ALL_URL = "https://steamspy.com/api.php?request=all&page={}"
    
    # Steam Store API
    STEAM_APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails?appids={}&cc=kr&l=korean"
    
    REQUEST_DELAY = 1.5  # Steam API rate limit 방지

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=500,
            help='Number of games to fetch (default: 500)'
        )
        parser.add_argument(
            '--top-rated',
            action='store_true',
            help='Sort by positive review ratio instead of player count'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.5,
            help='Delay between API requests (default: 1.5s)'
        )
        parser.add_argument(
            '--skip-details',
            action='store_true',
            help='Skip fetching detailed info from Steam (faster but less data)'
        )

    def fetch_steamspy_top_games(self, count):
        """SteamSpy에서 인기 게임 목록 가져오기"""
        all_games = {}
        
        # Top 100 in 2 weeks (가장 인기 있는 게임)
        self.stdout.write("📥 SteamSpy Top 100 (2주간 인기) 가져오는 중...")
        try:
            response = requests.get(self.STEAMSPY_TOP_URL, timeout=30)
            if response.status_code == 200:
                data = response.json()
                all_games.update(data)
                self.stdout.write(f"   ✅ Top 100: {len(data)}개")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   ⚠️ Top 100 실패: {e}"))
        
        time.sleep(2)
        
        # 추가 페이지에서 더 많은 게임 가져오기
        if count > 100:
            pages_needed = min((count - 100) // 1000 + 1, 5)  # 최대 5페이지
            for page in range(pages_needed):
                self.stdout.write(f"📥 SteamSpy 전체 목록 페이지 {page}...")
                try:
                    response = requests.get(
                        self.STEAMSPY_ALL_URL.format(page), 
                        timeout=60
                    )
                    if response.status_code == 200:
                        data = response.json()
                        all_games.update(data)
                        self.stdout.write(f"   ✅ 페이지 {page}: +{len(data)}개 (누적: {len(all_games)}개)")
                    time.sleep(3)  # SteamSpy rate limit
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"   ⚠️ 페이지 {page} 실패: {e}"))
                    break
        
        return all_games

    def fetch_steam_app_details(self, app_id):
        """Steam Store API에서 게임 상세 정보 가져오기"""
        try:
            response = requests.get(
                self.STEAM_APP_DETAILS_URL.format(app_id),
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                if data and str(app_id) in data and data[str(app_id)]['success']:
                    return data[str(app_id)]['data']
        except Exception:
            pass
        return None

    def handle(self, *args, **options):
        from games.models import Game
        
        count = options['count']
        top_rated = options['top_rated']
        self.REQUEST_DELAY = options['delay']
        skip_details = options['skip_details']
        
        self.stdout.write(self.style.NOTICE(
            f"🚀 Steam 인기 게임 {count}개 가져오기 시작"
        ))
        self.stdout.write(f"   📌 정렬: {'평점순' if top_rated else '플레이어 수 순'}")
        self.stdout.write(f"   📌 상세 정보: {'건너뜀' if skip_details else '가져옴'}")
        self.stdout.write("")
        
        # 기존 DB의 Steam App ID 수집
        existing_steam_ids = set(
            Game.objects.filter(
                steam_appid__isnull=False
            ).exclude(steam_appid=0).values_list('steam_appid', flat=True)
        )
        self.stdout.write(f"   📊 기존 DB 게임: {len(existing_steam_ids)}개")
        self.stdout.write("")
        
        # SteamSpy에서 게임 목록 가져오기
        steamspy_games = self.fetch_steamspy_top_games(count)
        
        if not steamspy_games:
            self.stdout.write(self.style.ERROR("❌ SteamSpy에서 데이터를 가져오지 못했습니다."))
            return
        
        # 정렬 (플레이어 수 또는 평점)
        games_list = []
        for app_id, data in steamspy_games.items():
            try:
                app_id_int = int(app_id)
                players = int(data.get('players', 0) or 0)
                positive = int(data.get('positive', 0) or 0)
                negative = int(data.get('negative', 0) or 0)
                
                total_reviews = positive + negative
                if total_reviews > 0:
                    positive_ratio = positive / total_reviews
                else:
                    positive_ratio = 0
                
                games_list.append({
                    'appid': app_id_int,
                    'name': data.get('name', ''),
                    'players': players,
                    'positive': positive,
                    'negative': negative,
                    'total_reviews': total_reviews,
                    'positive_ratio': positive_ratio,
                })
            except (ValueError, TypeError):
                continue
        
        # 정렬
        if top_rated:
            # 평점순 (최소 리뷰 1000개 이상)
            games_list = [g for g in games_list if g['total_reviews'] >= 1000]
            games_list.sort(key=lambda x: x['positive_ratio'], reverse=True)
        else:
            # 플레이어 수 순
            games_list.sort(key=lambda x: x['players'], reverse=True)
        
        self.stdout.write(f"\n📊 정렬 완료: {len(games_list)}개 게임")
        
        # 새 게임만 필터링
        new_games = []
        for game in games_list:
            if game['appid'] not in existing_steam_ids:
                new_games.append(game)
            if len(new_games) >= count:
                break
        
        self.stdout.write(f"   🆕 신규 게임: {len(new_games)}개")
        self.stdout.write("")
        
        if not new_games:
            self.stdout.write(self.style.WARNING("⚠️ 추가할 신규 게임이 없습니다."))
            return
        
        # DB에 저장
        created_count = 0
        skipped_count = 0
        
        for i, game_data in enumerate(new_games):
            app_id = game_data['appid']
            name = game_data['name']
            
            try:
                # 중복 체크
                if Game.objects.filter(steam_appid=app_id).exists():
                    skipped_count += 1
                    continue
                
                # Steam에서 상세 정보 가져오기 (선택적)
                image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg"
                description = ""
                metacritic_score = None
                
                if not skip_details:
                    details = self.fetch_steam_app_details(app_id)
                    if details:
                        name = details.get('name', name)
                        description = details.get('short_description', '')
                        if details.get('metacritic'):
                            metacritic_score = details['metacritic'].get('score')
                        if details.get('header_image'):
                            image_url = details['header_image']
                    time.sleep(self.REQUEST_DELAY)
                
                # 게임 생성
                Game.objects.create(
                    title=name[:200],
                    steam_appid=app_id,
                    image_url=image_url,
                    background_image=image_url,
                    description=description[:2000] if description else "",
                    metacritic_score=metacritic_score,
                )
                created_count += 1
                
                if (i + 1) % 50 == 0:
                    self.stdout.write(
                        f"   ✅ {i + 1}/{len(new_games)} 처리됨 "
                        f"(생성: {created_count}개)"
                    )
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"   ⚠️ '{name}' (ID: {app_id}) 저장 실패: {e}"
                ))
                skipped_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"\n🎉 완료!"))
        self.stdout.write(f"   ✅ 신규 생성: {created_count}개")
        self.stdout.write(f"   ⏭️ 건너뜀: {skipped_count}개")
        self.stdout.write(f"   📊 총 DB 게임 수: {Game.objects.count()}개")
