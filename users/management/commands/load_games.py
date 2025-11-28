import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from users.models import Game  # users 앱의 Game 모델 import

class Command(BaseCommand):
    help = 'Load games from JSON file'

    def handle(self, *args, **kwargs):
        # JSON 파일 경로 (프로젝트 최상위 폴더에 있다고 가정)
        file_path = os.path.join(settings.BASE_DIR, 'steam_sale_dataset_fast.json')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'JSON 파일을 찾을 수 없습니다: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR('JSON 파일 형식이 잘못되었습니다.'))
                return

        count = 0
        for item in data:
            # "app1028760" -> 1028760 변환
            try:
                steam_id_str = item.get('game_id', '').replace('app', '')
                if not steam_id_str.isdigit():
                    continue
                
                steam_appid = int(steam_id_str)
                
                # 이미 있으면 건너뛰거나 업데이트 (여기서는 get_or_create 사용)
                game, created = Game.objects.get_or_create(
                    steam_appid=steam_appid,
                    defaults={
                        'title': item.get('title', 'Unknown'),
                        'image_url': item.get('thumbnail', ''),
                        # JSON에 genre가 없으면 기본값 설정
                        'genre': 'Action' 
                    }
                )
                if created:
                    count += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"게임 저장 중 오류: {e}"))
                continue

        self.stdout.write(self.style.SUCCESS(f'총 {count}개의 게임을 DB에 저장했습니다!'))