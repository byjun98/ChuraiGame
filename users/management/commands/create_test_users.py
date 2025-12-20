"""
테스트용 어드민 계정 3개 생성 및 온보딩 데이터 입력

각 유저의 컨셉:
1. 하드코어 게이머 (hardcore_gamer) - 고난이도, 도전적인 게임 선호
   - Dark Souls류, 로그라이크, 전략 게임에 높은 점수
   - 캐주얼/편한 게임에 낮은 점수

2. 캐주얼 게이머 (casual_gamer) - 편안하고 힐링되는 게임 선호
   - 시뮬레이션, 힐링 게임에 높은 점수
   - 하드코어/폭력적 게임에 낮은 점수

3. 액션 게이머 (action_gamer) - AAA 액션/어드벤처 게임 선호
   - 스토리 중심 액션 게임에 높은 점수
   - 전략/시뮬레이션에 중간-낮은 점수

사용법:
    python manage.py create_test_users
    python manage.py create_test_users --delete  # 기존 테스트 유저 삭제 후 재생성
"""

import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from users.models import User, GameRating, OnboardingStatus
from games.models import Game


# 각 유저의 평가 패턴 정의
# 게임 타이틀의 키워드를 기반으로 점수 결정
USER_PROFILES = {
    'hardcore_gamer': {
        'username': 'test_hardcore',
        'email': 'hardcore@test.com',
        'nickname': '하드코어 마스터',
        'password': 'testpass123!',
        # 키워드별 선호도 (5: 쌍따봉, 3.5: 따봉, 0: 스킵, -1: 역따봉)
        'keywords_love': [  # 5점 (쌍따봉)
            'souls', 'dark', 'elden', 'sekiro', 'nioh', 'bloodborne',
            'roguelike', 'dead cells', 'hades', 'hollow knight',
            'blasphemous', 'celeste', 'cuphead', 'shovel knight',
            'xcom', 'civilization', 'crusader', 'paradox',
            'darkest dungeon', 'necrodancer', 'binding of isaac',
        ],
        'keywords_like': [  # 3.5점 (따봉)
            'metro', 'bioshock', 'control', 'prey', 'wolfenstein',
            'doom', 'quake', 'dishonored', 'hitman', 'deus ex',
            'witcher', 'mass effect', 'dragon age', 'baldur',
            'strategy', 'tactics', 'war', 'men of', 'total war',
            'frostpunk', 'rimworld', 'factorio', 'satisfactory',
        ],
        'keywords_dislike': [  # -1점 (역따봉)
            'farm', 'stardew', 'animal crossing', 'cozy',
            'relaxing', 'peaceful', 'cute', 'kawaii',
            'mobile', 'casual', 'match-3', 'hidden object',
            'sims', 'life sim',
        ],
    },
    'casual_gamer': {
        'username': 'test_casual',
        'email': 'casual@test.com',
        'nickname': '힐링 게이머',
        'password': 'testpass123!',
        'keywords_love': [  # 5점 (쌍따봉)
            'stardew', 'farm', 'cozy', 'relaxing', 'garden',
            'story', 'narrative', 'walking', 'adventure',
            'puzzle', 'building', 'sim', 'tycoon',
            'animal', 'cute', 'indie', 'pixel',
            'yoku', 'ori', 'planet', 'zoo',
        ],
        'keywords_like': [  # 3.5점 (따봉)
            'exploration', 'open world', 'rpg', 'quest',
            'platformer', 'metroid', 'sandbox', 'creative',
            'city', 'builder', 'management', 'business',
            'moonlighter', 'children', 'morta', 'fell seal',
        ],
        'keywords_dislike': [  # -1점 (역따봉)
            'souls', 'dark', 'hardcore', 'brutal', 'punish',
            'horror', 'gore', 'blood', 'violent', 'war',
            'shooter', 'fps', 'military', 'combat',
            'competitive', 'pvp', 'battle royale',
        ],
    },
    'action_gamer': {
        'username': 'test_action',
        'email': 'action@test.com',
        'nickname': 'AAA 액션러',
        'password': 'testpass123!',
        'keywords_love': [  # 5점 (쌍따봉)
            'action', 'adventure', 'gta', 'red dead', 'rockstar',
            'assassin', 'far cry', 'tomb raider', 'uncharted',
            'god of war', 'spider', 'batman', 'marvel', 'dc',
            'bioshock', 'control', 'alan wake', 'metro',
            'witcher', 'cyberpunk', 'horizon', 'ghost',
        ],
        'keywords_like': [  # 3.5점 (따봉)
            'rpg', 'story', 'cinematic', 'narrative',
            'open world', 'exploration', 'quest',
            'third person', 'combat', 'stealth',
            'shooter', 'fps', 'call of', 'battlefield',
        ],
        'keywords_dislike': [  # -1점 (역따봉)
            'strategy', 'turn-based', 'tactical', 'slow',
            '4x', 'grand strategy', 'simulation',
            'mobile', 'casual', 'match', 'puzzle',
            'text', 'visual novel',
        ],
    },
}


class Command(BaseCommand):
    help = '테스트용 어드민 계정 3개 생성 및 온보딩 데이터 입력'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='기존 테스트 유저 삭제 후 재생성',
        )

    def handle(self, *args, **options):
        # 1. 온보딩 게임 목록 로드
        json_path = os.path.join(settings.BASE_DIR, 'users', 'steam_sale_dataset_fast.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stderr.write(f"JSON 파일 로드 실패: {e}")
            return
        
        # 인기 게임 상위 100개 추출 (온보딩과 동일한 로직)
        quality_games = [
            g for g in data 
            if g.get('steam_rating', 0) >= 80 
            and g.get('review_count', 0) >= 1000
        ]
        sorted_games = sorted(quality_games, key=lambda x: x.get('review_count', 0), reverse=True)
        onboarding_games = sorted_games[:100]
        
        self.stdout.write(f"온보딩 게임 {len(onboarding_games)}개 로드됨")
        
        # 2. 기존 테스트 유저 삭제 (옵션)
        if options['delete']:
            usernames = [p['username'] for p in USER_PROFILES.values()]
            deleted_count, _ = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f"기존 테스트 유저 {deleted_count}개 삭제됨"))
        
        # 3. 각 유저 생성 및 평가 데이터 입력
        for profile_key, profile in USER_PROFILES.items():
            user, created = self._create_user(profile)
            if not created and not options['delete']:
                self.stdout.write(self.style.WARNING(
                    f"유저 '{profile['username']}' 이미 존재함. --delete 옵션 사용"
                ))
                continue
            
            # 평가 데이터 생성
            ratings_created = self._create_ratings(user, onboarding_games, profile)
            
            # 온보딩 상태 완료로 설정
            self._complete_onboarding(user, ratings_created)
            
            self.stdout.write(self.style.SUCCESS(
                f"✓ {profile['nickname']} ({profile['username']}) 생성 완료: {ratings_created}개 평가"
            ))
        
        # 4. 요약 출력
        self.stdout.write("\n" + "="*60)
        self.stdout.write("테스트 유저 생성 완료!")
        self.stdout.write("="*60)
        for profile_key, profile in USER_PROFILES.items():
            self.stdout.write(f"  - {profile['nickname']}: {profile['username']} / {profile['password']}")
        self.stdout.write("="*60)
        
        # 5. 유사도 계산 안내
        self.stdout.write("\n이제 유사도 계산을 실행하세요:")
        self.stdout.write("  python manage.py calculate_game_similarity")

    def _create_user(self, profile):
        """유저 생성"""
        user, created = User.objects.get_or_create(
            username=profile['username'],
            defaults={
                'email': profile['email'],
                'nickname': profile['nickname'],
                'is_staff': True,  # 어드민 권한
                'is_superuser': False,
            }
        )
        if created:
            user.set_password(profile['password'])
            user.save()
        return user, created

    def _create_ratings(self, user, games, profile):
        """게임 평가 데이터 생성"""
        ratings_count = 0
        keywords_love = [k.lower() for k in profile['keywords_love']]
        keywords_like = [k.lower() for k in profile['keywords_like']]
        keywords_dislike = [k.lower() for k in profile['keywords_dislike']]
        
        for game_data in games:
            title = game_data['title'].lower()
            steam_app_id = int(game_data['steam_app_id'])
            
            # 키워드 매칭으로 점수 결정
            score = self._determine_score(
                title, keywords_love, keywords_like, keywords_dislike
            )
            
            # 게임 생성 또는 조회
            game = self._get_or_create_game(game_data)
            
            # 평가 저장
            GameRating.objects.update_or_create(
                user=user,
                game=game,
                defaults={
                    'score': score,
                    'is_onboarding': True
                }
            )
            ratings_count += 1
        
        return ratings_count

    def _determine_score(self, title, keywords_love, keywords_like, keywords_dislike):
        """
        키워드 기반으로 점수 결정
        우선순위: 쌍따봉(5) > 역따봉(-1) > 따봉(3.5) > 스킵(0)
        """
        # 쌍따봉 체크 (최우선)
        for keyword in keywords_love:
            if keyword in title:
                return 5
        
        # 역따봉 체크 (싫어하는 것은 확실히 표시)
        for keyword in keywords_dislike:
            if keyword in title:
                return -1
        
        # 따봉 체크
        for keyword in keywords_like:
            if keyword in title:
                return 3.5
        
        # 매칭 없으면 랜덤하게 분배 (현실적인 데이터)
        import random
        rand = random.random()
        if rand < 0.3:
            return 3.5  # 30% 따봉
        elif rand < 0.4:
            return 5    # 10% 쌍따봉
        elif rand < 0.5:
            return -1   # 10% 역따봉
        else:
            return 0    # 50% 스킵

    def _get_or_create_game(self, game_data):
        """게임 생성 또는 조회"""
        steam_app_id = int(game_data['steam_app_id'])
        
        # rawg_id로 먼저 조회 (steam_app_id를 rawg_id로 사용)
        try:
            return Game.objects.get(rawg_id=steam_app_id)
        except Game.DoesNotExist:
            pass
        
        # steam_appid로 조회
        try:
            return Game.objects.get(steam_appid=steam_app_id)
        except Game.DoesNotExist:
            pass
        
        # 없으면 생성
        return Game.objects.create(
            rawg_id=steam_app_id,
            steam_appid=steam_app_id,
            title=game_data['title'],
            image_url=game_data.get('thumbnail', ''),
            metacritic_score=game_data.get('metacritic_score'),
            genre='Unknown'
        )

    def _complete_onboarding(self, user, total_ratings):
        """온보딩 완료 처리"""
        status, _ = OnboardingStatus.objects.update_or_create(
            user=user,
            defaults={
                'status': 'completed',
                'total_ratings': total_ratings,
                'started_at': timezone.now(),
                'completed_at': timezone.now()
            }
        )
        return status
