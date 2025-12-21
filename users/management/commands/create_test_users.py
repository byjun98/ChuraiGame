"""
테스트용 유저 20명 생성 및 대규모 온보딩 데이터(약 500개/인) 입력

각 유저별로 뚜렷한 페르소나(취향)를 부여하여 추천 시스템 성능 테스트에 적합하도록 구성함.
DB에 존재하는 게임 데이터를 활용.

사용법:
    python manage.py create_test_users
    python manage.py create_test_users --delete  # 기존 테스트 유저 삭제 후 재생성
"""

import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User, GameRating, OnboardingStatus
from games.models import Game
from django.db.models import Q

# 다양한 게이머 페르소나 정의 (20명)
USER_ARCHETYPES = [
    # 1. 장르별 매니아
    {
        'id': 'fps_pro',
        'nickname': '헤드슈터',
        'desc': 'FPS/슈팅 게임 매니아',
        'love': ['fps', 'shooter', 'action', 'call of duty', 'battlefield', 'counter-strike', 'doom', 'overwatch', 'apex'],
        'like': ['multiplayer', 'competitive', 'survival'],
        'dislike': ['puzzle', 'visual novel', 'turn-based', 'strategy', 'dating sim']
    },
    {
        'id': 'rpg_fanatic',
        'nickname': '만렙용사',
        'desc': '방대한 스토리의 RPG 선호',
        'love': ['rpg', 'open world', 'witcher', 'final fantasy', 'dragon quest', 'skyrim', 'fallout', 'mass effect'],
        'like': ['adventure', 'story', 'fantasy', 'action rpg', 'jrpg'],
        'dislike': ['sports', 'racing', 'match-3', 'casual']
    },
    {
        'id': 'strategy_general',
        'nickname': '제갈공명',
        'desc': '전략/시뮬레이션 게임 선호',
        'love': ['strategy', 'rts', 'turn-based', 'civilization', 'total war', 'xcom', 'paradox', 'stellaris', 'age of empires'],
        'like': ['simulation', 'management', 'city builder', 'tactical', 'history'],
        'dislike': ['platformer', 'fighting', 'fps', 'action']
    },
    {
        'id': 'horror_freak',
        'nickname': '강심장',
        'desc': '공포/스릴러 게임 매니아',
        'love': ['horror', 'survival horror', 'resident evil', 'silent hill', 'dead space', 'zombie', 'amnesia', 'outlast'],
        'like': ['thriller', 'dark', 'mystery', 'psychological', 'gore'],
        'dislike': ['family friendly', 'cute', 'sports', 'racing', 'comedy']
    },
    {
        'id': 'cozy_gamer',
        'nickname': '농장주인',
        'desc': '힐링/농장/시뮬레이션 선호',
        'love': ['farming', 'sim', 'stardew', 'animal crossing', 'harvest moon', 'cozy', 'relaxing', 'life sim'],
        'like': ['casual', 'cute', 'building', 'crafting', 'nature'],
        'dislike': ['horror', 'violence', 'shooter', 'hardcore', 'souls-like', 'gore']
    },
    
    # 2. 난이도/스타일별
    {
        'id': 'souls_masochist',
        'nickname': '유다희',
        'desc': '소울라이크/고난이도 게임 선호',
        'love': ['souls-like', 'dark souls', 'elden ring', 'bloodborne', 'sekiro', 'difficult', 'hardcore'],
        'like': ['action rpg', 'metroidvania', 'dark fantasy', 'boss rush'],
        'dislike': ['casual', 'easy', 'walking simulator', 'visual novel']
    },
    {
        'id': 'rogue_runner',
        'nickname': '무한루프',
        'desc': '로그라이크/로그라이트 선호',
        'love': ['roguelike', 'roguelite', 'permadeath', 'binding of isaac', 'hades', 'slay the spire', 'dead cells'],
        'like': ['dungeon crawler', 'indie', 'replay value', 'strategy'],
        'dislike': ['linear', 'narrative', 'sports', 'mmo']
    },
    {
        'id': 'retro_hipster',
        'nickname': '도트장인',
        'desc': '고전/픽셀아트/인디 게임 선호',
        'love': ['pixel graphics', 'retro', 'arcade', 'classic', '2d', 'platformer', 'metroidvania'],
        'like': ['indie', 'chiptune', 'side scroller', 'beat em up'],
        'dislike': ['aaa', 'fps', 'realistic', 'modern', 'battle royale']
    },
    {
        'id': 'story_bookworm',
        'nickname': '문학소년',
        'desc': '스토리/내러티브 중심 게임 선호',
        'love': ['story rich', 'narrative', 'visual novel', 'walking simulator', 'choose your own adventure', 'life is strange', 'telltale'],
        'like': ['point and click', 'adventure', 'atmospheric', 'mystery', 'singleplayer'],
        'dislike': ['multiplayer', 'competitive', 'sport', 'fighting', 'gameplay only']
    },
    {
        'id': 'junior_gamer',
        'nickname': '잼민이',
        'desc': '어린이/가족용 게임 선호',
        'love': ['family friendly', 'lego', 'minecraft', 'roblox', 'cartoon', 'platformer', 'mario', 'sonic'],
        'like': ['funny', 'colorful', 'adventure', 'co-op'],
        'dislike': ['horror', 'gore', 'sexual content', 'complex strategy', 'hardcore']
    },
    
    # 3. 기타 장르
    {
        'id': 'sports_fan',
        'nickname': '국대선수',
        'desc': '스포츠/레이싱 게임 선호',
        'love': ['sports', 'soccer', 'fifa', 'nba', 'madden', 'racing', 'forza', 'f1', 'baseball'],
        'like': ['simulation', 'competitive', 'multiplayer', 'management'],
        'dislike': ['fantasy', 'magic', 'rpg', 'horror', 'anime']
    },
    {
        'id': 'fighting_champ',
        'nickname': '철권고수',
        'desc': '격투/액션 게임 선호',
        'love': ['fighting', '2d fighter', '3d fighter', 'tekken', 'street fighter', 'mortal kombat', 'guilty gear'],
        'like': ['action', 'competitive', 'arcade', 'beat em up'],
        'dislike': ['strategy', 'slow', 'turn-based', 'puzzle']
    },
    {
        'id': 'puzzle_brain',
        'nickname': '두뇌풀가동',
        'desc': '퍼즐/두뇌 게임 선호',
        'love': ['puzzle', 'logic', 'portal', 'witness', 'tetris', 'mystery', 'brain teaser'],
        'like': ['casual', 'indie', 'relaxing', 'strategy', 'card game'],
        'dislike': ['action', 'shooter', 'reaction time', 'violent']
    },
    {
        'id': 'survival_expert',
        'nickname': '베어그릴스',
        'desc': '생존/크래프팅 게임 선호',
        'love': ['survival', 'crafting', 'open world', 'sandbox', 'rust', 'ark', 'forest', 'don\'t starve'],
        'like': ['building', 'exploration', 'adventure', 'multiplayer'],
        'dislike': ['linear', 'sport', 'puzzle', 'visual novel']
    },
    {
        'id': 'fantasy_lord',
        'nickname': '판타지군주',
        'desc': '하이 판타지/중세 배경 선호',
        'love': ['fantasy', 'magic', 'medieval', 'dragons', 'dungeons', 'sword', 'elves'],
        'like': ['rpg', 'adventure', 'strategy', 'mmo'],
        'dislike': ['sci-fi', 'futuristic', 'modern', 'guns', 'sports']
    },
    {
        'id': 'scifi_cyborg',
        'nickname': '미래전사',
        'desc': 'SF/미래/우주 배경 선호',
        'love': ['sci-fi', 'space', 'cyberpunk', 'futuristic', 'aliens', 'mechs', 'robots'],
        'like': ['shooter', 'strategy', 'rpg', 'exploration'],
        'dislike': ['medieval', 'historical', 'fantasy', 'farming']
    },
    
    # 4. 복합적 성향
    {
        'id': 'indie_snob',
        'nickname': '인디발굴단',
        'desc': '독창적인 인디 게임 선호',
        'love': ['indie', 'experimental', 'artistic', 'unique', 'stylized', 'short', 'masterpiece'],
        'like': ['platformer', 'puzzle', 'story'],
        'dislike': ['aaa', 'microtransactions', 'generic', 'pay to win']
    },
    {
        'id': 'female_casual',
        'nickname': '여성게이머',
        'desc': '여성 유저 선호 경향 (통계 기반)',
        'love': ['sims', 'stardew', 'story', 'puzzle', 'casual', 'co-op', 'overcooked', 'animal crossing'],
        'like': ['rpg', 'adventure', 'fantasy', 'decoration'],
        'dislike': ['war', 'military', 'hardcore', 'fps', 'sports']
    },
    {
        'id': 'action_adventure',
        'nickname': '탐험가',
        'desc': '액션 어드벤처 밸런스형',
        'love': ['action-adventure', 'zelda', 'uncharted', 'tomb raider', 'god of war', 'horizon', 'assassin'],
        'like': ['open world', 'story', 'puzzle', 'platformer'],
        'dislike': ['simulation', 'strategy', 'card game']
    },
    {
        'id': 'chaos_gamer',
        'nickname': '잡식게이머',
        'desc': '장르 불문 갓겜 선호',
        'love': ['masterpiece', 'great soundtrack', 'classic', 'overwhelmingly positive'],
        'like': ['indie', 'aaa', 'rpg', 'action', 'strategy', 'fps'],
        'dislike': ['bad', 'mixed', 'negative']
    }
]

class Command(BaseCommand):
    help = '20명의 상세 페르소나 테스트 유저 생성 (각 500개 평가)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='기존 테스트 유저 삭제 후 재생성',
        )

    def handle(self, *args, **options):
        # 1. DB에서 모든 게임 로드
        self.stdout.write("DB에서 게임 목록을 불러오는 중...")
        all_games = list(Game.objects.all().prefetch_related('tags'))
        
        if not all_games:
            self.stdout.write(self.style.ERROR("Error: DB에 게임 데이터가 없습니다. 먼저 게임 데이터를 적재해주세요."))
            return

        self.stdout.write(f"총 {len(all_games)}개의 게임이 로드되었습니다.")

        # 2. 기존 테스트 유저 삭제 (옵션)
        if options['delete']:
            usernames = [f"test_{p['id']}" for p in USER_ARCHETYPES]
            deleted_count, _ = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f"기존 테스트 유저 {deleted_count}명 삭제됨"))

        # 3. 유저 생성 및 데이터 입력
        total_created = 0
        
        for i, archetype in enumerate(USER_ARCHETYPES, 1):
            username = f"test_{archetype['id']}"
            email = f"{archetype['id']}@example.com"
            
            # 유저 생성
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'nickname': archetype['nickname'],
                    'is_staff': False, # 일반 유저로 생성
                    'is_superuser': False,
                }
            )
            
            if created:
                user.set_password('testpass123!')
                user.save()
            elif not options['delete']:
                self.stdout.write(f"[{i}/20] {user.nickname} 이미 존재함 (스킵)")
                continue

            # 평가 데이터 생성
            # 전체 게임 중 랜덤하게 500~600개를 선택하여 평가 (섞어서 다양성 확보)
            games_to_rate = random.sample(all_games, min(len(all_games), 600))
            
            created_count = self._create_ratings_for_user(user, games_to_rate, archetype)
            
            # 온보딩 완료 처리
            self._complete_onboarding(user, created_count)
            
            self.stdout.write(self.style.SUCCESS(
                f"[{i}/20] {user.nickname}({username}): {created_count}개 평가 생성 완료 ({archetype['desc']})"
            ))
            total_created += 1

        self.stdout.write(self.style.SUCCESS(f"\n총 {total_created}명의 테스트 유저 온보딩 데이터 생성 완료!"))
        self.stdout.write("비밀번호는 모두 'testpass123!' 입니다.")

    def _create_ratings_for_user(self, user, games, archetype):
        """유저 성향에 맞춰 게임 점수 매기기"""
        ratings_to_create = []
        
        # 성향 키워드 전처리
        loves = [k.lower() for k in archetype['love']]
        likes = [k.lower() for k in archetype['like']]
        dislikes = [k.lower() for k in archetype['dislike']]
        
        for game in games:
            # 점수 산정 로직
            score = 0
            
            # 게임 정보 추출 (제목 + (태그/장르가 있다면))
            title = game.title.lower()
            # 태그가 있는지 확인 (tags 관계형 필드 사용)
            tags = [t.slug.lower() for t in game.tags.all()] if hasattr(game, 'tags') else []
            # 레거시 장르 필드
            if game.genre:
                tags.append(game.genre.lower())
            
            # 검색 대상 텍스트
            search_text = title + " " + " ".join(tags)
            
            # 1. 싫어하는 장르 체크 (최우선)
            is_dislike = False
            for k in dislikes:
                if k in search_text:
                    if random.random() < 0.8: # 80% 확률로 싫어함
                        score = -1
                        is_dislike = True
                        break
            
            if is_dislike:
                # 역따봉 저장
                ratings_to_create.append(GameRating(
                    user=user, game=game, score=score, is_onboarding=True
                ))
                continue
                
            # 2. 좋아하는 장르 체크
            is_love = False
            for k in loves:
                if k in search_text:
                    is_love = True
                    break
            
            is_like = False
            if not is_love:
                for k in likes:
                    if k in search_text:
                        is_like = True
                        break
            
            # 점수 부여 (확률적)
            rand = random.random()
            
            if is_love:
                # Love 키워드 매칭 시: 60% 쌍따봉, 30% 따봉, 10% 스킵
                if rand < 0.6: score = 5
                elif rand < 0.9: score = 3.5
                else: score = 0
            elif is_like:
                # Like 키워드 매칭 시: 20% 쌍따봉, 60% 따봉, 20% 스킵
                if rand < 0.2: score = 5
                elif rand < 0.8: score = 3.5
                else: score = 0
            else:
                # 매칭 키워드 없을 시 (무관심/랜덤): 대부분 스킵
                # 5% 쌍따봉, 10% 따봉, 5% 역따봉, 80% 스킵
                if rand < 0.05: score = 5
                elif rand < 0.15: score = 3.5
                elif rand < 0.20: score = -1
                else: score = 0
            
            # 0점은 '평가 안함'과 같으므로 DB에 너무 많이 쌓이면 낭비일 수 있음.
            # 하지만 모델 정의상 score=0도 저장 가능. (SKIP)
            # 여기서는 편의상 0점도 저장.
            
            ratings_to_create.append(GameRating(
                user=user, game=game, score=score, is_onboarding=True
            ))

        # Bulk Create
        GameRating.objects.bulk_create(ratings_to_create, ignore_conflicts=True)
        
        return len(ratings_to_create)

    def _complete_onboarding(self, user, total_ratings):
        OnboardingStatus.objects.update_or_create(
            user=user,
            defaults={
                'status': 'completed',
                'total_ratings': total_ratings,
                'started_at': timezone.now(),
                'completed_at': timezone.now()
            }
        )
