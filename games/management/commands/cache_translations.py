
"""
게임 설명을 번역하여 DB에 캐싱하는 management command

사용법:
    python manage.py cache_translations
    python manage.py cache_translations --limit=50
    python manage.py cache_translations --force

이 스크립트는 DB에 있는 게임 중 description(영어)은 있지만 description_kr(한국어)이 없는 게임을 찾아
Gemini API를 사용하여 번역하고 저장합니다.
만약 description(영어)조차 없다면 RAWG API에서 설명을 먼저 가져옵니다.
"""

import time
from django.core.management.base import BaseCommand
from django.db.models import Q
from games.models import Game
from games.utils import update_game_with_rawg, translate_text_gemini

class Command(BaseCommand):
    help = 'Translate and cache game descriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of games to process'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-translation even if already exists'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Delay between API calls in seconds (default: 2.0s to respect limits)'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        force = options.get('force')
        delay = options.get('delay')
        
        # 대상 게임 선정: 
        # 1. 한국어 설명이 없는 게임
        # 2. 또는 force 옵션이 켜진 게임
        if force:
            games_to_process = Game.objects.all()
            self.stdout.write("⚠️  Force mode: Processing ALL games")
        else:
            games_to_process = Game.objects.filter(
                Q(description_kr__isnull=True) | Q(description_kr='')
            )
            
        if limit:
            games_to_process = games_to_process[:limit]
            
        total = games_to_process.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ All games already translated!'))
            return
            
        self.stdout.write(f"🔍 Found {total} games needing translation...")
        self.stdout.write(f"⏱️  Delay: {delay}s per request")
        
        success_count = 0
        failed_count = 0
        
        for i, game in enumerate(games_to_process):
            self.stdout.write(f"[{i+1}/{total}] Processing: {game.title}...", ending='')
            
            try:
                # 1. 영어 설명이 없으면 RAWG에서 가져오기
                if not game.description:
                    self.stdout.write(" (Fetch desc)...", ending='')
                    updated = update_game_with_rawg(game)
                    if not updated or not game.description:
                        self.stdout.write(self.style.WARNING(" ❌ No description found"))
                        failed_count += 1
                        continue
                
                # 2. 번역 실행
                self.stdout.write(" (Translating)...", ending='')
                translation = translate_text_gemini(game.description)
                
                if translation:
                    game.description_kr = translation
                    game.save(update_fields=['description_kr'])
                    self.stdout.write(self.style.SUCCESS(" ✅ Done"))
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR(" ❌ Translation failed"))
                    failed_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f" ❌ Error: {e}"))
                failed_count += 1
            
            # Rate limiting
            time.sleep(delay)
            
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("🎉 Translation cache completed!"))
        self.stdout.write(f"   ✅ Success: {success_count}")
        self.stdout.write(f"   ❌ Failed: {failed_count}")
        
        remaining = Game.objects.filter(Q(description_kr__isnull=True) | Q(description_kr='')).count()
        self.stdout.write(f"   📊 Remaining without translation: {remaining}")
