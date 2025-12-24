"""
중복 게임 정리 및 RAWG ID 누락 게임 재처리 스크립트

Usage:
    python manage.py cleanup_duplicate_games           # 중복 확인 (dry-run)
    python manage.py cleanup_duplicate_games --apply   # 실제 삭제 적용
    python manage.py cleanup_duplicate_games --fix-rawg  # RAWG ID 누락 게임 다시 fetch
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from games.models import Game


class Command(BaseCommand):
    help = '중복 게임 정리 및 RAWG ID 누락 게임 재처리'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='실제로 중복 게임 삭제 (기본값: dry-run)',
        )
        parser.add_argument(
            '--fix-rawg',
            action='store_true',
            help='RAWG ID가 없는 게임들 다시 fetch',
        )
        parser.add_argument(
            '--clear-invalid-rawg',
            action='store_true',
            help='잘못된 RAWG ID (Steam ID로 추정) 초기화',
        )
    
    def handle(self, *args, **options):
        if options['fix_rawg']:
            self._fix_rawg_ids()
        elif options['clear_invalid_rawg']:
            self._clear_invalid_rawg_ids()
        else:
            self._cleanup_duplicates(apply=options['apply'])
    
    def _cleanup_duplicates(self, apply=False):
        """중복 게임 정리"""
        self.stdout.write("중복 게임 검색 중...")
        
        # 영문 제목 추출하여 중복 찾기
        duplicates_found = {}
        
        all_games = Game.objects.all().order_by('id')
        
        for game in all_games:
            # 제목에서 영문 부분 추출
            title = game.title
            
            # "(영문제목)" 패턴 추출
            if '(' in title and ')' in title:
                # 괄호 안 영문 제목 추출
                import re
                match = re.search(r'\(([^)]+)\)', title)
                if match:
                    english_title = match.group(1).strip().lower()
                    
                    # 이미 있는지 확인
                    if english_title in duplicates_found:
                        duplicates_found[english_title].append(game)
                    else:
                        duplicates_found[english_title] = [game]
            
            # 순수 제목으로도 체크 (한글 제목)
            korean_title = title.split('(')[0].strip().lower()
            if korean_title and len(korean_title) > 2:  # 너무 짧은 건 제외
                if korean_title in duplicates_found:
                    # 이미 같은 영문 제목으로 추가되지 않았다면
                    if game not in duplicates_found[korean_title]:
                        duplicates_found[korean_title].append(game)
                else:
                    duplicates_found[korean_title] = [game]
        
        # 중복만 필터 (2개 이상인 것만)
        actual_duplicates = {k: v for k, v in duplicates_found.items() if len(v) > 1}
        
        if not actual_duplicates:
            self.stdout.write(self.style.SUCCESS("중복 게임 없음!"))
            return
        
        self.stdout.write(f"\n발견된 중복: {len(actual_duplicates)}개 그룹")
        self.stdout.write("=" * 60)
        
        # ID 기반 set으로 중복 추적 (같은 게임이 여러 그룹에서 삭제 대상이 되는 것 방지)
        game_ids_to_delete = set()
        game_ids_to_keep = set()
        
        for title, games in actual_duplicates.items():
            self.stdout.write(f"\n📌 '{title}' ({len(games)}개 중복)")
            
            # 가장 좋은 것 선택 (rawg_id, background_image, description 있는 것 우선)
            def score_game(g):
                score = 0
                if g.rawg_id:
                    score += 10
                if g.background_image:
                    score += 5
                if g.description and len(g.description) > 50:
                    score += 3
                if g.steam_appid:
                    score += 2
                if g.metacritic_score:
                    score += 2
                return score
            
            sorted_games = sorted(games, key=score_game, reverse=True)
            keep = sorted_games[0]
            duplicates = sorted_games[1:]
            
            self.stdout.write(f"  ✅ 유지: ID={keep.id}, rawg_id={keep.rawg_id}, steam={keep.steam_appid}")
            game_ids_to_keep.add(keep.id)
            
            for dup in duplicates:
                # 이미 다른 그룹에서 "유지"로 선택된 게임은 삭제하지 않음
                if dup.id not in game_ids_to_keep and dup.id not in game_ids_to_delete:
                    self.stdout.write(f"  ❌ 삭제: ID={dup.id}, rawg_id={dup.rawg_id}, steam={dup.steam_appid}")
                    game_ids_to_delete.add(dup.id)
        
        self.stdout.write("=" * 60)
        self.stdout.write(f"\n총 삭제 대상: {len(game_ids_to_delete)}개 게임")
        
        if apply:
            self.stdout.write("\n삭제 진행 중...")
            deleted_count = 0
            for game_id in game_ids_to_delete:
                try:
                    game = Game.objects.get(id=game_id)
                    game.delete()
                    deleted_count += 1
                except Game.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ ID={game_id} 이미 삭제됨"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ❌ ID={game_id} 삭제 실패: {e}"))
            self.stdout.write(self.style.SUCCESS(f"✅ {deleted_count}개 중복 게임 삭제 완료!"))
        else:
            self.stdout.write(self.style.WARNING("\n⚠️ Dry-run 모드입니다. 실제 삭제하려면 --apply 옵션을 추가하세요."))
    
    def _fix_rawg_ids(self):
        """RAWG ID가 없는 게임들 다시 fetch"""
        from games.utils import update_game_with_rawg
        import time
        
        # RAWG ID가 없거나 background_image가 없는 게임들
        games_to_fix = Game.objects.filter(rawg_id__isnull=True) | Game.objects.filter(background_image='')
        games_to_fix = games_to_fix.distinct()
        
        self.stdout.write(f"RAWG 데이터가 필요한 게임: {games_to_fix.count()}개")
        
        success_count = 0
        fail_count = 0
        
        for idx, game in enumerate(games_to_fix):
            self.stdout.write(f"[{idx+1}/{games_to_fix.count()}] {game.title}...")
            
            try:
                result = update_game_with_rawg(game, force_refresh=True)
                if result:
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✅ 완료"))
                else:
                    fail_count += 1
                    self.stdout.write(self.style.WARNING(f"  ⊘ 데이터 없음"))
            except Exception as e:
                fail_count += 1
                self.stdout.write(self.style.ERROR(f"  ❌ 오류: {e}"))
            
            time.sleep(0.5)  # Rate limiting
        
        self.stdout.write(f"\n완료: 성공 {success_count}개, 실패 {fail_count}개")
    
    def _clear_invalid_rawg_ids(self):
        """잘못된 RAWG ID (Steam ID로 추정되는 것들) 초기화"""
        
        # Steam App ID와 동일한 RAWG ID를 가진 게임들 찾기
        suspicious_games = []
        
        for game in Game.objects.filter(rawg_id__isnull=False, steam_appid__isnull=False):
            if game.rawg_id == game.steam_appid:
                suspicious_games.append(game)
        
        # RAWG ID가 100만 이상인 경우도 의심 (RAWG ID는 보통 100만 미만)
        for game in Game.objects.filter(rawg_id__gte=1000000):
            if game not in suspicious_games:
                suspicious_games.append(game)
        
        self.stdout.write(f"의심되는 게임: {len(suspicious_games)}개")
        
        for game in suspicious_games:
            self.stdout.write(f"  {game.title}: rawg_id={game.rawg_id}, steam_appid={game.steam_appid}")
            game.rawg_id = None
            game.save(update_fields=['rawg_id'])
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ {len(suspicious_games)}개 게임의 RAWG ID 초기화 완료"))
        self.stdout.write("다음 명령어로 다시 fetch하세요: python manage.py fetch_rawg_data")
