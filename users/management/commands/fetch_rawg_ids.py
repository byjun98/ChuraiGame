"""
Steam App ID -> RAWG ID 매핑 Command

세일 데이터셋의 각 게임에 대해 RAWG API를 호출하여
실제 RAWG ID와 slug를 조회하고 저장합니다.

사용법:
    python manage.py fetch_rawg_ids --test          # 샘플 테스트
    python manage.py fetch_rawg_ids --update-json   # JSON만 업데이트
    python manage.py fetch_rawg_ids --update-db     # DB만 업데이트
    python manage.py fetch_rawg_ids --all           # 전체 실행
"""

import os
import json
import time
import requests
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Steam App ID를 RAWG ID로 매핑하여 데이터셋과 DB 업데이트'
    
    RAWG_BASE_URL = 'https://api.rawg.io/api'
    REQUEST_DELAY = 0.1  # 100ms (Rate limit: 20 req/sec)
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='샘플 게임으로 RAWG API 테스트'
        )
        parser.add_argument(
            '--update-json',
            action='store_true',
            help='JSON 데이터셋 업데이트'
        )
        parser.add_argument(
            '--update-db',
            action='store_true',
            help='DB의 Game 모델 업데이트'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='JSON과 DB 모두 업데이트'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='처리할 게임 수 제한 (테스트용, 0=무제한)'
        )
    
    def get_rawg_api_key(self):
        """RAWG API 키 가져오기"""
        key = os.getenv('RAWG_API_KEY')
        if not key:
            # .env 파일에서 직접 읽기 시도
            env_path = os.path.join(settings.BASE_DIR, '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.startswith('RAWG_API_KEY='):
                            key = line.split('=', 1)[1].strip().strip('"\'')
                            break
        return key
    
    def search_game_on_rawg(self, title: str, steam_appid: str = None) -> dict:
        """
        RAWG API에서 게임 검색
        
        Returns:
            dict: {rawg_id, rawg_slug, rawg_name, matched} or None
        """
        api_key = self.get_rawg_api_key()
        if not api_key:
            return None
        
        try:
            # Steam store로 필터링하여 검색
            params = {
                'key': api_key,
                'search': title,
                'search_precise': 'true',
                'stores': '1',  # Steam store ID
                'page_size': 5
            }
            
            response = requests.get(
                f'{self.RAWG_BASE_URL}/games',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # 제목이 정확히 일치하는 게임 찾기
                    for game in results:
                        game_name = game.get('name', '').lower()
                        search_name = title.lower()
                        
                        # 정확히 일치하거나 매우 유사한 경우
                        game_clean = game_name.replace(':', '').replace('-', ' ').replace('  ', ' ')
                        search_clean = search_name.replace(':', '').replace('-', ' ').replace('  ', ' ')
                        
                        if game_name == search_name or game_clean == search_clean:
                            return {
                                'rawg_id': game['id'],
                                'rawg_slug': game['slug'],
                                'rawg_name': game['name'],
                                'matched': 'exact'
                            }
                    
                    # 첫 번째 결과 반환 (부분 매칭)
                    first = results[0]
                    return {
                        'rawg_id': first['id'],
                        'rawg_slug': first['slug'],
                        'rawg_name': first['name'],
                        'matched': 'first_result'
                    }
            elif response.status_code == 401:
                self.stderr.write(self.style.ERROR(f"❌ API 키가 유효하지 않습니다"))
                return None
            
            return None
            
        except requests.RequestException as e:
            self.stderr.write(f"  ⚠️ API 요청 실패: {e}")
            return None
    
    def run_test(self):
        """샘플 게임으로 RAWG API 테스트"""
        test_games = [
            ("Lost Judgment", "2058190"),
            ("Elden Ring", "1245620"),
            ("BioShock", "7670"),
            ("Frostpunk", "323190"),
            ("Control Ultimate Edition", "870780"),
        ]
        
        self.stdout.write("\n🧪 샘플 테스트:\n")
        
        for title, steam_id in test_games:
            self.stdout.write(f"  📍 {title} (Steam: {steam_id}):")
            result = self.search_game_on_rawg(title, steam_id)
            
            if result:
                self.stdout.write(self.style.SUCCESS(f"    ✅ RAWG ID: {result['rawg_id']}"))
                self.stdout.write(f"    📝 Slug: {result['rawg_slug']}")
                self.stdout.write(f"    🎮 Name: {result['rawg_name']}")
                self.stdout.write(f"    🔗 URL: https://rawg.io/games/{result['rawg_slug']}")
            else:
                self.stdout.write(self.style.ERROR("    ❌ 찾을 수 없음"))
            self.stdout.write("")
            time.sleep(self.REQUEST_DELAY)
    
    def update_json_dataset(self, limit=0):
        """세일 데이터셋에 RAWG ID 추가"""
        json_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
        backup_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast_backup.json')
        
        self.stdout.write(f"\n📂 데이터셋 로드: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            games = json.load(f)
        
        # 백업 생성
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
        self.stdout.write(f"💾 백업 생성: {backup_path}")
        
        total = len(games)
        if limit > 0:
            total = min(total, limit)
        
        updated = 0
        failed = 0
        skipped = 0
        
        self.stdout.write(f"\n🔍 {total}개 게임에서 RAWG ID 조회 시작...\n")
        
        for i, game in enumerate(games):
            if limit > 0 and i >= limit:
                break
                
            title = game.get('title', '')
            steam_appid = game.get('steam_app_id', '')
            
            # 이미 rawg_id가 있으면 스킵 (재실행 시 효율성)
            if game.get('rawg_id') and game.get('rawg_slug'):
                skipped += 1
                continue
            
            self.stdout.write(f"[{i+1}/{total}] {title[:40]:<40} (Steam: {steam_appid})...", ending=" ")
            
            result = self.search_game_on_rawg(title, steam_appid)
            
            if result:
                game['rawg_id'] = result['rawg_id']
                game['rawg_slug'] = result['rawg_slug']
                game['rawg_name'] = result['rawg_name']
                self.stdout.write(self.style.SUCCESS(f"✅ {result['rawg_id']} ({result['matched']})"))
                updated += 1
            else:
                self.stdout.write(self.style.WARNING("❌ 못찾음"))
                failed += 1
            
            # Rate limit 방지
            time.sleep(self.REQUEST_DELAY)
            
            # 진행상황 저장 (100개마다)
            if (i + 1) % 100 == 0:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(games, f, ensure_ascii=False, indent=2)
                self.stdout.write(f"\n💾 중간 저장 완료 ({i+1}/{total})\n")
        
        # 최종 저장
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(self.style.SUCCESS(f"✅ JSON 업데이트 완료!"))
        self.stdout.write(f"   - 업데이트: {updated}개")
        self.stdout.write(f"   - 실패: {failed}개")
        self.stdout.write(f"   - 스킵 (이미 있음): {skipped}개")
        self.stdout.write(f"{'='*50}\n")
        
        return {'updated': updated, 'failed': failed, 'skipped': skipped}
    
    def update_database(self):
        """DB의 Game 모델에 RAWG ID 업데이트"""
        from games.models import Game
        
        json_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
        
        with open(json_path, 'r', encoding='utf-8') as f:
            games_data = json.load(f)
        
        # Steam App ID -> RAWG 정보 매핑
        steam_to_rawg = {}
        for game in games_data:
            steam_appid = game.get('steam_app_id')
            rawg_id = game.get('rawg_id')
            if steam_appid and rawg_id:
                steam_to_rawg[int(steam_appid)] = {
                    'rawg_id': rawg_id,
                    'rawg_slug': game.get('rawg_slug', '')
                }
        
        self.stdout.write(f"\n📊 매핑 데이터: {len(steam_to_rawg)}개")
        
        # DB 업데이트
        updated = 0
        db_games = Game.objects.filter(steam_appid__isnull=False)
        
        self.stdout.write(f"🎮 DB 게임 수: {db_games.count()}개\n")
        
        for game in db_games:
            if game.steam_appid in steam_to_rawg:
                mapping = steam_to_rawg[game.steam_appid]
                old_rawg_id = game.rawg_id
                
                # rawg_id가 Steam App ID와 같거나 None이면 업데이트
                if game.rawg_id == game.steam_appid or game.rawg_id is None:
                    game.rawg_id = mapping['rawg_id']
                    game.save(update_fields=['rawg_id'])
                    self.stdout.write(f"  ✅ {game.title}: {old_rawg_id} -> {mapping['rawg_id']}")
                    updated += 1
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ DB 업데이트 완료: {updated}개"))
        return updated
    
    def handle(self, *args, **options):
        api_key = self.get_rawg_api_key()
        
        if not api_key:
            self.stderr.write(self.style.ERROR("❌ RAWG_API_KEY가 설정되지 않았습니다."))
            self.stderr.write("   .env 파일에 RAWG_API_KEY=your_key 를 추가하세요.")
            return
        
        self.stdout.write(f"🔑 RAWG API Key: {'*' * 20}...{api_key[-4:]}")
        
        if options['test']:
            self.run_test()
        elif options['update_json']:
            self.update_json_dataset(limit=options['limit'])
        elif options['update_db']:
            self.update_database()
        elif options['all']:
            self.update_json_dataset(limit=options['limit'])
            self.update_database()
        else:
            self.stdout.write("\n사용법:")
            self.stdout.write("  python manage.py fetch_rawg_ids --test         # 샘플 테스트")
            self.stdout.write("  python manage.py fetch_rawg_ids --update-json  # JSON 업데이트")
            self.stdout.write("  python manage.py fetch_rawg_ids --update-db    # DB 업데이트")
            self.stdout.write("  python manage.py fetch_rawg_ids --all          # 전체 실행")
            self.stdout.write("  python manage.py fetch_rawg_ids --all --limit 10  # 10개만 테스트")
            self.stdout.write("\n먼저 --test 로 동작을 확인하세요.\n")
