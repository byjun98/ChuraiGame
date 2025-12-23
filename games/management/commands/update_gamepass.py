"""
Xbox Game Pass 데이터 업데이트 명령어

PC 게임패스에 포함된 게임들을 조회하여 DB의 Game 모델에 is_on_gamepass 플래그를 업데이트합니다.

사용법:
    python manage.py update_gamepass
"""

from django.core.management.base import BaseCommand
from games.models import Game
import requests
import time
import re


class Command(BaseCommand):
    help = 'Xbox Game Pass(PC) 게임 목록을 가져와서 DB에 표시합니다.'
    
    # PC 게임패스 카탈로그 ID
    CATALOG_ID_PC = "fdd9e2a7-0fee-49f6-ad69-4354098401ff"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='모든 게임의 is_on_gamepass를 False로 초기화 후 업데이트'
        )
    
    def get_game_ids(self):
        """게임패스에 등록된 게임들의 ID 목록을 가져옵니다."""
        url = "https://catalog.gamepass.com/sigls/v2"
        params = {
            "id": self.CATALOG_ID_PC,
            "language": "ko-kr",
            "market": "KR"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # id가 있는 객체만 추출 (보통 1번째 인덱스부터 실제 게임 ID)
            game_ids = [item['id'] for item in data if len(item.get('id', '')) > 10]
            
            # 첫번째 ID는 카탈로그 자체의 ID이므로 제외
            return game_ids[1:] if len(game_ids) > 1 else game_ids
            
        except Exception as e:
            self.stderr.write(f"게임패스 ID 목록 조회 실패: {e}")
            return []
    
    def get_game_details(self, id_list):
        """ID 리스트를 받아 게임 상세 정보(특히 제목)를 조회합니다."""
        base_url = "https://displaycatalog.mp.microsoft.com/v7.0/products"
        
        results = []
        batch_size = 20
        
        self.stdout.write(f"   총 {len(id_list)}개의 게임 정보 조회 중...")
        
        for i in range(0, len(id_list), batch_size):
            batch = id_list[i:i + batch_size]
            id_str = ",".join(batch)
            
            params = {
                "bigIds": id_str,
                "market": "KR",
                "languages": "ko-kr",
                "MS-CV": "DGU1mcuYo0WMMp+F.1"
            }
            
            try:
                res = requests.get(base_url, params=params, timeout=30)
                res.raise_for_status()
                data = res.json()
                
                for product in data.get('Products', []):
                    localized = product.get('LocalizedProperties', [{}])[0]
                    title = localized.get('ProductTitle', '')
                    
                    if title:
                        results.append({
                            'title': title,
                            'store_id': product.get('ProductId'),
                        })
                        
            except Exception as e:
                self.stderr.write(f"   배치 {i} 조회 실패: {e}")
                
            # 서버 부하 방지
            time.sleep(0.3)
            
            # 진행 상황 표시
            if (i // batch_size + 1) % 5 == 0:
                self.stdout.write(f"   ... {min(i + batch_size, len(id_list))}/{len(id_list)} 완료")
        
        return results
    
    def normalize_title(self, title):
        """게임 제목 정규화 (매칭용)"""
        if not title:
            return ""
        # 소문자 변환, 특수문자 제거, 공백 정리
        normalized = title.lower()
        normalized = re.sub(r'[®™©:\-–—\'\"!?\(\)]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🎮 Xbox Game Pass (PC) 데이터 업데이트 시작"))
        self.stdout.write("")
        
        # 1. 리셋 옵션 처리
        if options['reset']:
            reset_count = Game.objects.filter(is_on_gamepass=True).update(is_on_gamepass=False)
            self.stdout.write(f"   ♻️ {reset_count}개 게임의 게임패스 상태 초기화 완료")
        
        # 2. 게임패스 게임 ID 목록 가져오기
        self.stdout.write("📡 1단계: 게임패스 게임 ID 목록 조회 중...")
        game_ids = self.get_game_ids()
        
        if not game_ids:
            self.stderr.write(self.style.ERROR("   게임패스 게임 목록을 가져올 수 없습니다."))
            return
        
        self.stdout.write(f"   ✅ {len(game_ids)}개의 게임 ID 발견")
        
        # 3. 게임 상세 정보 가져오기
        self.stdout.write("")
        self.stdout.write("📥 2단계: 게임 상세 정보 조회 중...")
        gamepass_games = self.get_game_details(game_ids)
        
        if not gamepass_games:
            self.stderr.write(self.style.ERROR("   게임 상세 정보를 가져올 수 없습니다."))
            return
        
        self.stdout.write(f"   ✅ {len(gamepass_games)}개의 게임 정보 수집 완료")
        
        # 4. DB 게임과 매칭
        self.stdout.write("")
        self.stdout.write("🔄 3단계: DB 게임과 매칭 중...")
        
        # 게임패스 게임 제목 정규화
        gamepass_titles = set()
        gamepass_title_map = {}  # 정규화된 제목 -> 원본 제목
        
        for game in gamepass_games:
            normalized = self.normalize_title(game['title'])
            gamepass_titles.add(normalized)
            gamepass_title_map[normalized] = game['title']
        
        # DB에서 모든 게임 가져오기
        all_games = Game.objects.all()
        matched_count = 0
        matched_games = []
        
        for game in all_games:
            normalized_db_title = self.normalize_title(game.title)
            
            # 정확히 일치하는 경우
            if normalized_db_title in gamepass_titles:
                if not game.is_on_gamepass:
                    game.is_on_gamepass = True
                    game.save(update_fields=['is_on_gamepass'])
                matched_count += 1
                matched_games.append(game.title)
                continue
            
            # 부분 일치 (DB 제목이 게임패스 제목에 포함되거나 그 반대)
            for gp_title in gamepass_titles:
                if len(normalized_db_title) >= 5 and len(gp_title) >= 5:
                    if normalized_db_title in gp_title or gp_title in normalized_db_title:
                        if not game.is_on_gamepass:
                            game.is_on_gamepass = True
                            game.save(update_fields=['is_on_gamepass'])
                        matched_count += 1
                        matched_games.append(f"{game.title} (← {gamepass_title_map.get(gp_title, gp_title)})")
                        break
        
        # 5. 결과 출력
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"✅ 완료! {matched_count}개의 게임이 게임패스에 포함됨으로 표시됨"))
        
        if matched_games:
            self.stdout.write("")
            self.stdout.write("📋 매칭된 게임 목록 (상위 20개):")
            for title in matched_games[:20]:
                self.stdout.write(f"   • {title}")
            
            if len(matched_games) > 20:
                self.stdout.write(f"   ... 외 {len(matched_games) - 20}개")
        
        self.stdout.write("")
        self.stdout.write(f"💡 게임 상세 페이지에서 '🎮 Game Pass' 뱃지가 표시됩니다.")
