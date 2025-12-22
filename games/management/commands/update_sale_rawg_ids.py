"""
세일 JSON 파일에 rawg_id 추가

DB의 steam_appid -> rawg_id 매핑을 사용해서
steam_sale_dataset_fast.json에 rawg_id 필드를 추가합니다.

사용법:
    python manage.py update_sale_rawg_ids
"""

import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from games.models import Game


class Command(BaseCommand):
    help = 'DB의 rawg_id를 세일 JSON 파일에 추가'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 파일을 수정하지 않고 결과만 미리보기'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # JSON 파일 경로
        json_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f'❌ JSON 파일을 찾을 수 없습니다: {json_path}'))
            return
        
        self.stdout.write(f"📂 JSON 파일: {json_path}")
        
        # DB에서 steam_appid -> rawg_id 매핑 생성
        self.stdout.write("🔍 DB에서 매핑 데이터 로드 중...")
        
        steam_to_rawg = {}
        games_with_both = Game.objects.filter(
            steam_appid__isnull=False,
            rawg_id__isnull=False
        ).values_list('steam_appid', 'rawg_id')
        
        for steam_appid, rawg_id in games_with_both:
            steam_to_rawg[str(steam_appid)] = rawg_id
        
        self.stdout.write(f"   ✅ DB에서 {len(steam_to_rawg)}개의 매핑 발견")
        
        # JSON 파일 로드
        self.stdout.write("📖 JSON 파일 로드 중...")
        with open(json_path, 'r', encoding='utf-8') as f:
            sale_data = json.load(f)
        
        total = len(sale_data)
        self.stdout.write(f"   ✅ {total}개의 세일 게임 로드됨")
        
        # rawg_id 추가
        matched = 0
        unmatched = 0
        already_has = 0
        unmatched_games = []
        
        for game in sale_data:
            steam_app_id = game.get('steam_app_id', '')
            
            # 이미 rawg_id가 있는 경우
            if game.get('rawg_id'):
                already_has += 1
                continue
            
            # DB에서 매핑 찾기
            rawg_id = steam_to_rawg.get(steam_app_id)
            
            if rawg_id:
                game['rawg_id'] = rawg_id
                matched += 1
            else:
                unmatched += 1
                if unmatched <= 10:  # 처음 10개만 표시
                    unmatched_games.append(f"  - {game.get('title', 'Unknown')} (Steam: {steam_app_id})")
        
        # 결과 출력
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("📊 결과:"))
        self.stdout.write(f"   ✅ 새로 매칭됨: {matched}개")
        self.stdout.write(f"   ⏭️  이미 있음: {already_has}개")
        self.stdout.write(f"   ❌ 매칭 실패: {unmatched}개 (DB에 rawg_id 없음)")
        
        if unmatched_games:
            self.stdout.write("")
            self.stdout.write("📋 매칭 실패 게임 (처음 10개):")
            for game in unmatched_games:
                self.stdout.write(game)
        
        # 파일 저장
        if dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("🔸 [DRY-RUN] 실제로 파일을 수정하지 않았습니다."))
            self.stdout.write("   실제 수정하려면: python manage.py update_sale_rawg_ids")
        else:
            if matched > 0:
                # 백업 생성
                backup_path = json_path + '.backup'
                with open(backup_path, 'w', encoding='utf-8') as f:
                    with open(json_path, 'r', encoding='utf-8') as orig:
                        f.write(orig.read())
                self.stdout.write(f"   💾 백업 생성: {backup_path}")
                
                # 수정된 파일 저장
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(sale_data, f, ensure_ascii=False, indent=2)
                
                self.stdout.write("")
                self.stdout.write(self.style.SUCCESS(f"✅ JSON 파일 업데이트 완료! ({matched}개 rawg_id 추가)"))
            else:
                self.stdout.write("")
                self.stdout.write(self.style.WARNING("⚠️ 추가할 rawg_id가 없습니다."))
        
        # 매칭률 계산
        match_rate = (matched + already_has) / total * 100 if total > 0 else 0
        self.stdout.write("")
        self.stdout.write(f"📈 전체 매칭률: {match_rate:.1f}% ({matched + already_has}/{total})")
        
        if unmatched > 0:
            self.stdout.write("")
            self.stdout.write(self.style.NOTICE(
                "💡 매칭 실패 게임들은 'fetch_rawg_data' 명령어로 RAWG 데이터를 가져온 후 다시 실행하세요."
            ))
