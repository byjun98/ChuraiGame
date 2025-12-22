"""
Steam 사용자 태그 크롤링 Management Command

Steam 상점 페이지에서 유저들이 정의한 인기 태그를 크롤링하여 저장합니다.
예: 소울라이크(Souls-like), 힐링(Relaxing), 심리적 공포(Psychological Horror) 등

사용법:
    python manage.py fetch_steam_tags              # 전체 게임 (한글 태그)
    python manage.py fetch_steam_tags --english    # 영어 태그 (추천 알고리즘용)
    python manage.py fetch_steam_tags --limit=100  # 100개 게임만
    python manage.py fetch_steam_tags --force      # 기존 태그 있어도 재수집

참고: beautifulsoup4 필요
    pip install beautifulsoup4
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import models
from games.models import Game, Tag


class Command(BaseCommand):
    help = '스팀 상점 페이지에서 유저들이 정의한 인기 태그를 크롤링하여 저장합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='처리할 게임 수 제한 (기본: 전체)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='요청 간 딜레이 (초, 기본: 1.0 - 스팀 서버 부하 방지)'
        )
        parser.add_argument(
            '--english',
            action='store_true',
            help='영어 태그로 수집 (추천 알고리즘 매칭용)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='이미 태그가 있는 게임도 다시 수집'
        )
        parser.add_argument(
            '--max-tags',
            type=int,
            default=10,
            help='게임당 최대 태그 수 (기본: 10)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        delay = options['delay']
        use_english = options['english']
        force = options['force']
        max_tags = options['max_tags']

        # Steam App ID가 있는 게임만 필터링
        games = Game.objects.filter(steam_appid__isnull=False)
        
        # 이미 태그가 있는 게임 제외 (force가 아닌 경우)
        if not force:
            # 태그가 3개 미만인 게임만 대상
            games = games.annotate(
                tag_count=models.Count('tags')
            ).filter(tag_count__lt=10)
        
        if limit:
            games = games[:limit]
        
        total = games.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('처리할 게임이 없습니다.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*70}'))
        self.stdout.write(self.style.SUCCESS(f'  Steam 사용자 태그 크롤링'))
        self.stdout.write(self.style.SUCCESS(f'{"="*70}'))
        self.stdout.write(f'대상 게임: {total}개')
        self.stdout.write(f'언어: {"영어 (English)" if use_english else "한국어 (Korean)"}')
        self.stdout.write(f'게임당 최대 태그: {max_tags}개')
        self.stdout.write(f'딜레이: {delay}초')
        self.stdout.write(f'예상 소요 시간: ~{int(total * delay / 60 + 1)}분')
        self.stdout.write(self.style.SUCCESS(f'{"="*70}\n'))

        # 성인 인증(Age Gate) 우회 쿠키
        cookies = {
            'birthtime': '631152001',  # 1990년생
            'lastagecheckage': '1-0-1990',
            'wants_mature_content': '1',
            'mature_content': '1',
        }
        
        # 언어 설정
        if use_english:
            cookies['Steam_Language'] = 'english'
        else:
            cookies['Steam_Language'] = 'koreana'
        
        # 브라우저 헤더 (봇 차단 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5' if use_english else 'ko-KR,ko;q=0.9',
        }

        stats = {
            'success': 0,
            'no_tags': 0,
            'error': 0,
            'total_tags_added': 0
        }

        for idx, game in enumerate(games, 1):
            try:
                count = self.update_game_tags(game, cookies, headers, max_tags)
                
                if count > 0:
                    stats['success'] += 1
                    stats['total_tags_added'] += count
                    self.stdout.write(
                        self.style.SUCCESS(f'[{idx}/{total}] ✅ {game.title}: {count}개 태그 추가')
                    )
                else:
                    stats['no_tags'] += 1
                    self.stdout.write(
                        self.style.WARNING(f'[{idx}/{total}] ⚠️  {game.title}: 태그 없음')
                    )
            except Exception as e:
                stats['error'] += 1
                self.stdout.write(
                    self.style.ERROR(f'[{idx}/{total}] ❌ {game.title}: {str(e)}')
                )
            
            time.sleep(delay)

        # 결과 요약
        self.stdout.write(self.style.SUCCESS(f'\n{"="*70}'))
        self.stdout.write(self.style.SUCCESS(f'  크롤링 완료!'))
        self.stdout.write(self.style.SUCCESS(f'{"="*70}'))
        self.stdout.write(f'✅ 성공: {stats["success"]}개 게임')
        self.stdout.write(f'⚠️  태그 없음: {stats["no_tags"]}개 게임')
        self.stdout.write(f'❌ 실패: {stats["error"]}개 게임')
        self.stdout.write(f'🏷️  총 추가된 태그: {stats["total_tags_added"]}개')
        self.stdout.write(f'📊 DB 전체 태그 수: {Tag.objects.count()}개')
        self.stdout.write(self.style.SUCCESS(f'{"="*70}\n'))

    def update_game_tags(self, game, cookies, headers, max_tags):
        """
        특정 게임의 Steam 태그를 크롤링하여 저장
        
        Returns:
            int: 추가된 태그 수
        """
        app_id = game.steam_appid
        url = f"https://store.steampowered.com/app/{app_id}/"

        response = requests.get(
            url, 
            cookies=cookies, 
            headers=headers, 
            timeout=15,
            allow_redirects=True
        )
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        # 나이 인증 페이지로 리다이렉트된 경우 체크
        if 'agecheck' in response.url:
            raise Exception("Age gate 우회 실패")

        soup = BeautifulSoup(response.text, 'html.parser')

        # 스팀 상점 페이지의 '인기 태그' 영역
        # 클래스: .app_tag (glance_tags popular_tags 내부)
        tag_elements = soup.select('.app_tag')
        
        if not tag_elements:
            # 대체 선택자 시도
            tag_elements = soup.select('.popular_tags .app_tag')
        
        if not tag_elements:
            return 0

        new_tags = []
        for tag_el in tag_elements:
            tag_text = tag_el.get_text(strip=True)
            
            # 쓸모없는 태그 제외
            if tag_text in ['+', '', ' ']:
                continue
            
            # 너무 긴 태그 제외 (보통 버그)
            if len(tag_text) > 50:
                continue
                
            new_tags.append(tag_text)

        # 상위 N개만 사용
        top_tags = new_tags[:max_tags]
        
        if not top_tags:
            return 0

        added_count = 0
        
        for tag_name in top_tags:
            # slug 생성 (영어가 아닌 경우 해싱)
            slug = self.create_slug(tag_name)
            
            # 태그 유형 결정
            tag_type = self.determine_tag_type(tag_name)
            
            # Tag 객체 가져오거나 생성
            tag, created = Tag.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': tag_name,
                    'tag_type': tag_type,
                    'weight': 1.0
                }
            )
            
            # 게임에 태그 추가 (이미 있으면 무시됨)
            if tag not in game.tags.all():
                game.tags.add(tag)
                added_count += 1
        
        return added_count

    def create_slug(self, tag_name):
        """
        태그 이름으로 slug 생성
        한글의 경우 영어 변환 시도, 안 되면 해시
        """
        # 먼저 기본 slugify 시도
        slug = slugify(tag_name, allow_unicode=False)
        
        if slug:
            return slug[:50]  # 최대 50자
        
        # 한글 등 특수 문자의 경우, 해시 기반 slug
        import hashlib
        hash_suffix = hashlib.md5(tag_name.encode()).hexdigest()[:8]
        
        # 영어 문자만 추출
        english_part = re.sub(r'[^a-zA-Z0-9\s]', '', tag_name)
        english_slug = slugify(english_part) if english_part else ''
        
        if english_slug:
            return f"{english_slug[:40]}-{hash_suffix}"
        else:
            return f"tag-{hash_suffix}"

    def determine_tag_type(self, tag_name):
        """
        태그 이름으로 태그 유형 결정
        """
        tag_lower = tag_name.lower()
        
        # 장르 키워드
        genre_keywords = [
            'rpg', 'fps', 'action', 'adventure', 'shooter', 'platformer', 
            'strategy', 'simulation', 'racing', 'sports', 'puzzle', 
            'roguelike', 'roguelite', 'metroidvania', 'souls-like', 'soulslike',
            'mmorpg', 'moba', 'rts', 'turn-based', '액션', '어드벤처', '롤플레잉',
            '슈터', '전략', '시뮬레이션', '퍼즐', '플랫포머', '로그라이크'
        ]
        
        # 테마 키워드
        theme_keywords = [
            'horror', 'fantasy', 'sci-fi', 'cyberpunk', 'medieval', 'space',
            'zombie', 'post-apocalyptic', 'steampunk', 'anime', 'cartoon',
            '공포', '판타지', '사이버펑크', '중세', '좀비', '종말'
        ]
        
        # 분위기 키워드
        mood_keywords = [
            'relaxing', 'difficult', 'challenging', 'casual', 'hardcore',
            'atmospheric', 'funny', 'cute', 'dark', 'emotional', 'colorful',
            '힐링', '편안', '어려움', '캐주얼', '하드코어', '귀여운', '어두운'
        ]
        
        for keyword in genre_keywords:
            if keyword in tag_lower:
                return 'genre'
        
        for keyword in theme_keywords:
            if keyword in tag_lower:
                return 'theme'
        
        for keyword in mood_keywords:
            if keyword in tag_lower:
                return 'mood'
        
        # 기본값: feature
        return 'feature'
