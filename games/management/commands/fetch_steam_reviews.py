"""
Steam 리뷰 크롤링 Management Command

Steam Store API를 사용하여 게임별 한국어 리뷰를 수집합니다.

사용법:
    python manage.py fetch_steam_reviews              # 전체 게임
    python manage.py fetch_steam_reviews --limit=100  # 100개 게임만
    python manage.py fetch_steam_reviews --reviews=10 # 게임당 10개 리뷰
    python manage.py fetch_steam_reviews --force      # 기존 리뷰 있어도 추가 수집

데이터 출처: Steam Store API
URL: https://store.steampowered.com/appreviews/{app_id}?json=1&language=koreana
"""

import requests
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from games.models import Game, SteamReview


class Command(BaseCommand):
    help = 'Steam에서 게임별로 한국어 리뷰를 크롤링하여 DB에 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='크롤링할 게임 수 제한 (기본: 전체)'
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=5,
            help='게임당 가져올 리뷰 수 (기본: 5개)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.3,
            help='API 요청 간 딜레이 (초, 기본: 0.3)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='이미 리뷰가 있는 게임도 다시 수집'
        )
        parser.add_argument(
            '--min-length',
            type=int,
            default=20,
            help='최소 리뷰 길이 (기본: 20자)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        reviews_per_game = options['reviews']
        delay = options['delay']
        force = options['force']
        min_length = options['min_length']

        # Steam App ID가 있는 게임만 필터링
        games = Game.objects.filter(steam_appid__isnull=False)
        
        # 이미 리뷰가 있는 게임 제외 (force가 아닌 경우)
        if not force:
            games_with_reviews = SteamReview.objects.values_list('game_id', flat=True).distinct()
            games = games.exclude(id__in=games_with_reviews)
        
        if limit:
            games = games[:limit]
        
        total = games.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('크롤링할 게임이 없습니다.'))
            if not force:
                self.stdout.write('이미 모든 게임에 리뷰가 있습니다. --force 옵션으로 다시 수집할 수 있습니다.')
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*70}'))
        self.stdout.write(self.style.SUCCESS(f'  Steam 리뷰 크롤링 시작'))
        self.stdout.write(self.style.SUCCESS(f'{"="*70}'))
        self.stdout.write(f'대상 게임: {total}개')
        self.stdout.write(f'게임당 리뷰: {reviews_per_game}개')
        self.stdout.write(f'최소 리뷰 길이: {min_length}자')
        self.stdout.write(f'예상 소요 시간: ~{int(total * delay / 60 + 1)}분')
        self.stdout.write(self.style.SUCCESS(f'{"="*70}\n'))

        stats = {
            'success': 0,
            'no_reviews': 0,
            'error': 0,
            'total_reviews': 0
        }

        for idx, game in enumerate(games, 1):
            count = self.fetch_reviews_for_game(
                game, 
                reviews_per_game, 
                min_length
            )
            
            if count > 0:
                stats['success'] += 1
                stats['total_reviews'] += count
                self.stdout.write(
                    self.style.SUCCESS(f'[{idx}/{total}] ✅ {game.title}: {count}개 리뷰 저장')
                )
            elif count == 0:
                stats['no_reviews'] += 1
                self.stdout.write(
                    self.style.WARNING(f'[{idx}/{total}] ⚠️  {game.title}: 한국어 리뷰 없음')
                )
            else:
                stats['error'] += 1
                self.stdout.write(
                    self.style.ERROR(f'[{idx}/{total}] ❌ {game.title}: 크롤링 실패')
                )
            
            # API 차단 방지 딜레이
            time.sleep(delay)

        # 결과 요약
        self.stdout.write(self.style.SUCCESS(f'\n{"="*70}'))
        self.stdout.write(self.style.SUCCESS(f'  크롤링 완료!'))
        self.stdout.write(self.style.SUCCESS(f'{"="*70}'))
        self.stdout.write(f'✅ 성공: {stats["success"]}개 게임')
        self.stdout.write(f'⚠️  리뷰 없음: {stats["no_reviews"]}개 게임')
        self.stdout.write(f'❌ 실패: {stats["error"]}개 게임')
        self.stdout.write(f'📝 총 저장된 리뷰: {stats["total_reviews"]}개')
        self.stdout.write(self.style.SUCCESS(f'{"="*70}\n'))

    def fetch_reviews_for_game(self, game, num_reviews, min_length):
        """
        특정 게임의 Steam 리뷰를 가져와 저장
        
        Returns:
            int: 저장된 리뷰 수 (-1 = 에러)
        """
        app_id = game.steam_appid
        url = f"https://store.steampowered.com/appreviews/{app_id}"
        
        params = {
            'json': 1,
            'filter': 'updated',      # 최신 수정된 리뷰 순
            'language': 'koreana',    # 한국어 리뷰만
            'num_per_page': num_reviews * 2,  # 여유 있게 가져오기 (필터링 고려)
            'purchase_type': 'all',   # 스팀 구매 + 키 등록 모두
            'review_type': 'all'      # 긍정/부정 모두
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return -1
            
            data = response.json()

            if data.get('success') != 1:
                return -1
            
            reviews_data = data.get('reviews', [])
            
            if not reviews_data:
                return 0

            saved_count = 0

            for item in reviews_data:
                if saved_count >= num_reviews:
                    break
                
                # 리뷰 ID (중복 체크용)
                review_id = item.get('recommendationid', '')
                if not review_id:
                    continue
                
                # 이미 저장된 리뷰면 스킵
                if SteamReview.objects.filter(steam_review_id=review_id).exists():
                    continue
                
                # 리뷰 내용
                content = item.get('review', '').strip()
                
                # 너무 짧은 리뷰 스킵
                if len(content) < min_length:
                    continue
                
                # 작성자 정보
                author_data = item.get('author', {})
                steam_author_id = author_data.get('steamid', 'unknown')
                playtime_forever = author_data.get('playtime_forever', 0) // 60  # 분→시간
                playtime_at_review = author_data.get('playtime_at_review', 0) // 60
                
                # 평가 정보
                is_recommended = item.get('voted_up', True)
                votes_up = item.get('votes_up', 0)
                votes_funny = item.get('votes_funny', 0)
                
                # 시간 정보
                timestamp_created = None
                timestamp_updated = None
                
                if item.get('timestamp_created'):
                    timestamp_created = timezone.make_aware(
                        datetime.fromtimestamp(item['timestamp_created'])
                    )
                if item.get('timestamp_updated'):
                    timestamp_updated = timezone.make_aware(
                        datetime.fromtimestamp(item['timestamp_updated'])
                    )
                
                # DB 저장
                try:
                    SteamReview.objects.create(
                        game=game,
                        steam_review_id=review_id,
                        steam_author_id=steam_author_id,
                        author_playtime_hours=playtime_forever,
                        author_playtime_at_review=playtime_at_review,
                        content=content,
                        is_recommended=is_recommended,
                        votes_up=votes_up,
                        votes_funny=votes_funny,
                        timestamp_created=timestamp_created,
                        timestamp_updated=timestamp_updated,
                    )
                    saved_count += 1
                except Exception as e:
                    # 중복 등 에러는 무시
                    pass
            
            return saved_count

        except requests.Timeout:
            return -1
        except Exception as e:
            return -1
