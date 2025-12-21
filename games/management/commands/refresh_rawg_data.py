"""
RAWG 데이터 새로고침 명령

DB에 저장된 모든 게임의 데이터를 RAWG API에서 다시 가져와 업데이트합니다.
- description, background_image, genre, metacritic_score 업데이트
- 스크린샷 새로 가져오기

Usage:
    python manage.py refresh_rawg_data
    python manage.py refresh_rawg_data --limit 10  # 10개만 테스트
"""

import os
import time
import requests
from django.core.management.base import BaseCommand
from games.models import Game, GameScreenshot
from dotenv import load_dotenv

load_dotenv()

RAWG_API_KEY = os.getenv('RAWG_API_KEY')
REQUEST_DELAY = 0.15  # 150ms delay between requests


class Command(BaseCommand):
    help = 'Refresh all game data from RAWG API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='Limit number of games to process (0 = all)'
        )
        parser.add_argument(
            '--skip-screenshots',
            action='store_true',
            help='Skip screenshot updates'
        )

    def handle(self, *args, **options):
        if not RAWG_API_KEY:
            self.stderr.write(self.style.ERROR('RAWG_API_KEY not found in environment'))
            return

        limit = options['limit']
        skip_screenshots = options['skip_screenshots']

        # rawg_id가 있는 게임만 가져오기
        games = Game.objects.filter(rawg_id__isnull=False).exclude(rawg_id=0)
        
        if limit > 0:
            games = games[:limit]

        total = games.count()
        self.stdout.write(f'Processing {total} games with RAWG IDs...\n')

        updated = 0
        errors = 0

        for i, game in enumerate(games, 1):
            try:
                self.stdout.write(f'[{i}/{total}] {game.title} (RAWG ID: {game.rawg_id})... ', ending='')
                
                # RAWG API에서 게임 정보 가져오기
                url = f'https://api.rawg.io/api/games/{game.rawg_id}?key={RAWG_API_KEY}'
                response = requests.get(url, timeout=10)
                
                if response.status_code != 200:
                    self.stdout.write(self.style.WARNING(f'API Error {response.status_code}'))
                    errors += 1
                    time.sleep(REQUEST_DELAY)
                    continue

                data = response.json()

                # 데이터 업데이트
                game.description = data.get('description_raw', '') or data.get('description', '')
                game.background_image = data.get('background_image', '')
                if not game.image_url:
                    game.image_url = data.get('background_image', '')
                
                # 장르
                genres = data.get('genres', [])
                if genres:
                    game.genre = ', '.join([g['name'] for g in genres[:3]])
                
                # 메타크리틱
                if data.get('metacritic'):
                    game.metacritic_score = data.get('metacritic')

                game.save()

                # 스크린샷 업데이트
                if not skip_screenshots:
                    time.sleep(REQUEST_DELAY)
                    ss_url = f'https://api.rawg.io/api/games/{game.rawg_id}/screenshots?key={RAWG_API_KEY}&page_size=8'
                    ss_response = requests.get(ss_url, timeout=10)
                    
                    if ss_response.status_code == 200:
                        ss_data = ss_response.json()
                        screenshots = ss_data.get('results', [])
                        
                        if screenshots:
                            # 기존 스크린샷 삭제 후 새로 추가
                            GameScreenshot.objects.filter(game=game).delete()
                            for ss in screenshots:
                                if ss.get('image'):
                                    GameScreenshot.objects.create(
                                        game=game,
                                        image_url=ss['image']
                                    )

                self.stdout.write(self.style.SUCCESS('OK'))
                updated += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {e}'))
                errors += 1

            time.sleep(REQUEST_DELAY)

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS(f'Updated: {updated} games'))
        if errors:
            self.stdout.write(self.style.WARNING(f'Errors: {errors} games'))
        self.stdout.write('=' * 50)
