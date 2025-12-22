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

# 다양한 게이머 페르소나 정의 (67명)
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
        'love': ['roguelike', 'roguelite', 'permadeath', 'binding of isaac', 'hades', 'dead cells'],
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
        'nickname': '운동선수',
        'desc': '스포츠 게임 선호',
        'love': ['sports', 'soccer', 'fifa', 'nba', 'madden', 'baseball'],
        'like': ['simulation', 'competitive', 'multiplayer', 'management'],
        'dislike': ['fantasy', 'magic', 'rpg', 'horror', 'anime']
    },
    {
        'id': 'racer',
        'nickname': '레이서',
        'desc': '레이싱 게임 선호',
        'love': ['racing', 'drving', 'forza', 'f1'],
        'like': ['simulation', 'competitive', 'multiplayer', 'management'],
        'dislike': ['turn=based', 'strategy', 'rpg', 'puzzle', 'horror']
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
    {
        'id': 'card_strategy',
        'nickname': '카드마스터',
        'desc': '카드/로그라이크/로그라이트/턴제 게임 선호',
        'love': ['roguelike', 'roguelite', 'strategy', 'card battler', 'card game', 'turn-based', 'deckbuilding', 'slay the spire',],
        'like': ['indie', 'dungeon crawler', 'replay value'],
        'dislike': ['relaxing', 'sport', 'linear', 'mmo']
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
        'id': 'top_gamer',
        'nickname': '갓겜만함',
        'desc': '장르 불문 갓겜 선호',
        'love': ['masterpiece', 'great soundtrack', 'classic', 'overwhelmingly positive'],
        'like': ['indie', 'aaa', 'rpg', 'action', 'strategy', 'fps'],
        'dislike': ['bad', 'mixed', 'negative']
    },
    {
        'id': 'funny_co-op',
        'nickname': '똥믈리에',
        'desc': '협동/똥겜 선호',
        'love': ['multiplayer', 'co-op', 'online co-op', 'funny'],
        'like': ['physics', 'atmospheric', 'adventure', 'indie'],
        'dislike': ['rpg', 'mmo', 'pay to win', 'aaa']
    },
    {
        'id': 'nostalgia_gamer',
        'nickname': '추억보정',
        'desc': '추억의 명작 재플레이',
        'love': ['remaster', 'classic', 'old school'],
        'like': ['jrpg', 'retro'],
        'dislike': ['live service']
    },

    # 5. 플레이 성향/소비 성향 기반
    { 
        'id': 'achievement_hunter',
        'nickname': '도전과제헌터',
        'desc': '업적/100% 클리어 집착형',
        'love': ['achievements', 'completionist', '100 percent', 'challenge'],
        'like': ['singleplayer', 'hard mode', 'replay'],
        'dislike': ['early access', 'buggy', 'unfinished']
    },
    {
        'id': 'speed_runner',
        'nickname': '스피드광',
        'desc': '스피드런/최적화 플레이 선호',
        'love': ['speedrun', 'glitch', 'optimization', 'time attack'],
        'like': ['platformer', 'action', 'precision'],
        'dislike': ['rng', 'slow pacing', 'long cutscene']
    },
    {
        'id': 'sandbox_creator',
        'nickname': '창조신',
        'desc': '샌드박스/창작 중심 플레이',
        'love': ['sandbox', 'creative mode', 'modding', 'building'],
        'like': ['simulation', 'crafting'],
        'dislike': ['linear', 'story only']
    },
    {
        'id': 'mod_lover',
        'nickname': '모드없인못살아',
        'desc': '모드 커뮤니티 중심 유저',
        'love': ['mods', 'community', 'custom content'],
        'like': ['rpg', 'sandbox', 'strategy'],
        'dislike': ['closed platform', 'no mod support']
    },
    {
        'id': 'early_access_tester',
        'nickname': '얼리요정',
        'desc': '얼리액세스/인디 실험작 선호',
        'love': ['early access', 'alpha', 'beta', 'experimental'],
        'like': ['indie', 'survival', 'roguelike'],
        'dislike': ['finished only', 'story spoiler']
    },

    # 6. 멀티플레이/소셜 중심
    {
        'id': 'party_gamer',
        'nickname': '파티피플',
        'desc': '여럿이 즐기는 파티 게임 선호',
        'love': ['party game', 'local multiplayer', 'overcooked', 'moving out'],
        'like': ['co-op', 'funny', 'casual'],
        'dislike': ['singleplayer', 'long story']
    },
    {
        'id': 'voice_chat_social',
        'nickname': '수다쟁이',
        'desc': '음성채팅 기반 소셜 플레이',
        'love': ['voice chat', 'social', 'multiplayer'],
        'like': ['mmo', 'co-op', 'survival'],
        'dislike': ['solo', 'mute']
    },
    {
        'id': 'guild_mmo',
        'nickname': '길드인간',
        'desc': 'MMO 길드/레이드 중심',
        'love': ['mmo', 'raid', 'guild', 'endgame'],
        'like': ['rpg', 'fantasy', 'support role'],
        'dislike': ['solo', 'short game']
    },
    {
        'id': 'pvp_competitor',
        'nickname': '랭겜중독',
        'desc': 'PVP/랭크 경쟁 중심',
        'love': ['pvp', 'ranked', 'ladder', 'esports'],
        'like': ['fps', 'moba', 'fighting'],
        'dislike': ['story', 'pve only']
    },

    # 7. 특정 하위 장르 특화
    {
        'id': 'moba_addict',
        'nickname': '라인서기',
        'desc': 'MOBA 장르 선호',
        'love': ['moba', 'league of legends', 'dota', 'teamfight'],
        'like': ['competitive', 'team play'],
        'dislike': ['singleplayer', 'story']
    },
    {
        'id': 'auto_battler',
        'nickname': '오토장인',
        'desc': '오토배틀러/자동 전투 선호',
        'love': ['auto battler', 'tft', 'team comp'],
        'like': ['strategy', 'rng'],
        'dislike': ['manual action']
    },
    {
        'id': 'idle_gamer',
        'nickname': '방치왕',
        'desc': '방치형/클리커 게임 선호',
        'love': ['idle', 'incremental', 'clicker'],
        'like': ['numbers go up', 'casual'],
        'dislike': ['action', 'precision']
    },
    {
        'id': 'rhythm_master',
        'nickname': '박자충',
        'desc': '리듬/음악 게임 선호',
        'love': ['rhythm', 'music', 'beat', 'osu', 'djmax'],
        'like': ['arcade', 'score attack'],
        'dislike': ['story', 'slow']
    },
    {
        'id': 'stealth_shadow',
        'nickname': '암살자',
        'desc': '스텔스 플레이 선호',
        'love': ['stealth', 'assassin', 'hitman', 'thief'],
        'like': ['tactical', 'singleplayer'],
        'dislike': ['loud', 'horde combat']
    },
    {
        'id': 'historical_buff',
        'nickname': '역사덕후',
        'desc': '역사 기반/실존 배경 게임 선호',
        'love': ['historical', 'history', 'real events', 'medieval', 'ancient', 'ww2'],
        'like': ['strategy', 'simulation', 'tactical', 'grand strategy'],
        'dislike': ['fantasy', 'magic', 'sci-fi']
    },
    {
        'id': 'economy_tycoon',
        'nickname': '경제지배자',
        'desc': '경제/경영/재테크 시뮬레이션 선호',
        'love': ['economy', 'tycoon', 'management', 'trading', 'capitalism'],
        'like': ['simulation', 'city builder', 'strategy'],
        'dislike': ['action', 'fps', 'story driven']
    },
    {
        'id': 'cinematic_lover',
        'nickname': '영화체험러',
        'desc': '연출·그래픽·몰입감 중시',
        'love': ['cinematic', 'immersive', 'high graphics', 'realistic'],
        'like': ['action-adventure', 'story rich', 'singleplayer'],
        'dislike': ['pixel', 'retro', 'low fidelity']
    },
    {
        'id': 'one_shot_gamer',
        'nickname': '한방러',
        'desc': '짧고 강렬한 단편 게임 선호',
        'love': ['short game', 'one sitting', '2~5 hours', 'compact'],
        'like': ['indie', 'experimental', 'story'],
        'dislike': ['open world', 'grind', 'live service']
    },

    # 8. 테마/분위기 중심
    {
        'id': 'post_apocalypse',
        'nickname': '종말론자',
        'desc': '포스트 아포칼립스 세계관 선호',
        'love': ['post apocalypse', 'wasteland', 'ruins'],
        'like': ['survival', 'rpg'],
        'dislike': ['cute', 'cozy']
    },
    {
        'id': 'detective_mind',
        'nickname': '명탐정',
        'desc': '추리/수사 중심 게임 선호',
        'love': ['detective', 'investigation', 'case solving'],
        'like': ['story', 'mystery'],
        'dislike': ['action heavy']
    },
    {
        'id': 'dark_fantasy',
        'nickname': '어둠추종자',
        'desc': '다크 판타지 세계관 선호',
        'love': ['dark fantasy', 'grim', 'curse'],
        'like': ['souls-like', 'rpg'],
        'dislike': ['bright', 'cartoon']
    },
    {
        'id': 'cute_collector',
        'nickname': '귀여움수집가',
        'desc': '캐릭터 수집/귀여운 비주얼',
        'love': ['cute', 'collecting', 'gacha'],
        'like': ['casual', 'rpg'],
        'dislike': ['hardcore', 'realistic']
    },

    # 9. 플랫폼/환경 기반
    {
        'id': 'mobile_only',
        'nickname': '모바일전사',
        'desc': '모바일 게임 위주',
        'love': ['mobile', 'touch', 'short session'],
        'like': ['idle', 'gacha', 'puzzle'],
        'dislike': ['pc only', 'complex ui']
    },
    {
        'id': 'controller_gamer',
        'nickname': '패드충',
        'desc': '패드 플레이 최적화 선호',
        'love': ['controller', 'console'],
        'like': ['action', 'racing'],
        'dislike': ['mouse precision']
    },
    {
        'id': 'vr_explorer',
        'nickname': '현실탈출자',
        'desc': 'VR 게임 선호',
        'love': ['vr', 'immersion', 'motion'],
        'like': ['simulation', 'rhythm'],
        'dislike': ['flat screen only']
    },
    {
        'id': 'low_spec_gamer',
        'nickname': '저사양의희망',
        'desc': '저사양 PC 게임 선호',
        'love': ['low spec', '2d', 'pixel'],
        'like': ['indie'],
        'dislike': ['high end', 'ray tracing']
    },

    # 10. 한국인이라면 해봤을 게임
    {
        'id': 'k_online_native',
        'nickname': '민속놀이장인',
        'desc': '한국형 온라인/경쟁 게임만 선호 (스팀/콘솔 경험 없음)',
        'love': [
            'maplestory', 'grand chase', 'latale', 'sudden attack',
            'fifa', 'fc online', 'dungeon fighter', 'dnf',
            'talesrunner', 'kartrider', 'ghost online', 'soul saver',
            'nexus', 'baram', 'lineage', 'aion', 'blade & soul', 'bns',
            'league of legends', 'lol', 'valorant', 'overwatch', 'starcraft',
            'mmo', 'mmorpg', 'online', 'esports', 'moba', 'competitive', 'multiplayer'
        ],
        'like': ['free to play', 'f2p', 'co-op', 'team', 'ranking', 'social', 'raid'],
        'dislike': [
            'indie', 'singleplayer', 'visual novel', 'walking simulator',
            'interactive movie', 'turn-based', 'puzzle', 'rich story',
            'controller', 'local co-op'
        ]
    },
    {
        'id': 'k_casual_rpg',
        'nickname': '헤네시스주민',
        'desc': '메이플/라테일 등 아기자기한 2D/횡스크롤 RPG 선호',
        'love': [
            'maplestory', 'latale', 'talesrunner', 'grand chase', 'ghost online',
            'cute', 'pixel graphics', '2d', 'platformer', 'side scroller',
            'anime', 'co-op', 'casual', 'character customization'
        ],
        'like': ['fantasy', 'adventure', 'relaxing', 'social'],
        'dislike': ['horror', 'realistic', 'fps', 'gore', 'military']
    },
    {
        'id': 'k_competitive',
        'nickname': '미드오픈',
        'desc': '롤/서든/발로란트 등 남을 이겨야 하는 경쟁 게임 선호',
        'love': [
            'league of legends', 'lol', 'valorant', 'overwatch', 'sudden attack',
            'starcraft', 'pubg', 'fifa', 'fc online', 'kartrider',
            'competitive', 'multiplayer', 'esports', 'fps', 'moba',
            'rts', 'pvp', 'team-based', 'strategy', 'fast-paced'
        ],
        'like': ['shooter', 'action', 'battle royale', 'sports'],
        'dislike': ['turn-based', 'walking simulator', 'visual novel', 'slow', 'story rich']
    },
    {
        'id': 'k_hardcore_mmo',
        'nickname': '통제구역',
        'desc': '리니지/던파/로아 등 장비 맞추고 스펙업하는 RPG 선호',
        'love': [
            'lineage', 'dungeon fighter', 'dnf', 'lost ark', 'blade & soul',
            'aion', 'nexus: the kingdom of the winds', 'baram',
            'mmorpg', 'action rpg', 'hack and slash', 'loot', 'grinding',
            'open world', 'raid', 'fantasy', 'class-based'
        ],
        'like': ['co-op', 'dungeon crawler', 'magic', 'medieval'],
        'dislike': ['puzzle', 'platformer', 'casual', 'cute', 'pixel graphics']
    },
    {
        'id': 'hack_and_slash_fan',
        'nickname': '모코코',
        'desc': '로스트아크/디아블로/던파 등 핵앤슬래시 액션 선호',
        'love': [
            'lost ark', 'loa', 'diablo', 'path of exile', 'poe',
            'dungeon fighter', 'dnf', 'mu online', 'undecember',
            'hack and slash', 'isometric', 'action rpg', 'loot',
            'dungeon crawler', 'boss rush', 'co-op', 'fantasy'
        ],
        'like': ['mmorpg', 'online', 'great soundtrack'],
        'dislike': ['fps', 'sport', 'turn-based strategy', 'slow']
    },
    {
        'id': 'high_graphic_action',
        'nickname': '그래픽장인',
        'desc': '검은사막/블소/마영전 등 고화질 커스터마이징 & 액션 선호',
        'love': [
            'black desert', 'bdo', 'blade & soul', 'bns',
            'vindictus', 'mabinogi heroes', 'elyon', 'tera', 'archeage',
            'open world', 'character customization', 'action',
            'beautiful', 'sandbox', 'mmorpg', 'pvp', 'female protagonist'
        ],
        'like': ['exploration', 'adventure', 'fantasy', 'jiggle physics'],
        'dislike': ['pixel graphics', '2d', 'retro', 'low poly']
    },
    {
        'id': 'lineage_like_lord',
        'nickname': '서버랭커',
        'desc': '오딘/리니지W/나이트크로우 등 전쟁/세력전 선호',
        'love': [
            'lineage', 'odin: valhalla rising', 'odin', 'night crows',
            'prasia electric', 'wars of prasia', 'mir4', 'mir m',
            'hit2', 'v4', 'dk online', 'r2', 'eos',
            'mmorpg', 'massively multiplayer', 'war', 'pvp',
            'guild', 'economy', 'medieval', 'political'
        ],
        'like': ['auto battler', 'idle', 'management', 'rpg'],
        'dislike': ['puzzle', 'platformer', 'arcade', 'cute', 'story rich']
    },
    {
        'id': 'anime_otaku',
        'nickname': '십덕후',
        'desc': '원신/블루아카이브/니케 등 서브컬처/카툰렌더링 선호',
        'love': [
            'genshin impact', 'honkai', 'star rail', 'blue archive',
            'nikke', 'umamusume', 'fate/grand order', 'fgo',
            'epic seven', 'cookie run: kingdom', 'tower of fantasy',
            'anime', 'jrpg', 'visual novel', 'story rich',
            'waifu', 'turn-based', 'gacha', 'singleplayer'
        ],
        'like': ['open world', 'action rpg', 'soundtrack', 'cute'],
        'dislike': ['realistic', 'military', 'western', 'sports', 'horror']
    },
    {
        'id': 'pc_bang_warrior',
        'nickname': '피시방죽돌이',
        'desc': '피파/서든/배그/옵치 등 남들과 경쟁하는 인기 게임 선호',
        'love': [
            'fc online', 'fifa', 'sudden attack', 'pubg', 'battlegrounds',
            'overwatch', 'valorant', 'league of legends', 'starcraft',
            'kartrider drift', 'cyphers', 'crazy arcade',
            'multiplayer', 'competitive', 'esports', 'shooter',
            'fps', 'sports', 'soccer', 'team-based', 'pvp', 'ranking'
        ],
        'like': ['action', 'simulation', 'strategy', 'co-op'],
        'dislike': ['singleplayer', 'indie', 'walking simulator', 'text based']
    },
    {
        'id': 'social_life_sim',
        'nickname': '음유시인',
        'desc': '마비노기/동숲/쿠키런 등 힐링/생활/꾸미기 선호',
        'love': [
            'mabinogi', 'animal crossing', 'the sims', 'cookie run',
            'alice closet', 'love nikki', 'zepeto', 'play together',
            'life sim', 'farming sim', 'crafting', 'building',
            'cute', 'social', 'relaxing', 'casual', 'open world'
        ],
        'like': ['rpg', 'fantasy', 'adventure', 'co-op'],
        'dislike': ['horror', 'gore', 'violence', 'difficult', 'competitive']
    },

    # 11. 모바일 게임 중심
    {
        'id': 'mobile_rogue_survivor',
        'nickname': '탕탕특공대원',
        'desc': '탕탕특공대/궁수의전설/운빨존많겜 등 로그라이트 슈팅/디펜스 선호',
        'love': [
            'survivor.io', 'tangtang', 'archero', 'lucky defense', 'random dice',
            'brawl stars', 'vampire survivors', 'magic survival',
            'roguelite', 'bullet hell', 'tower defense', 'auto battler',
            'casual', 'arcade', 'replay value', 'strategy'
        ],
        'like': ['roguelike', 'action', 'indie', 'pixel graphics', '2d'],
        'dislike': ['story rich', 'visual novel', 'slow', 'realistic', 'simulation']
    },
    {
        'id': 'mobile_subculture',
        'nickname': '지휘관',
        'desc': '니케/원신/명조/브라운더스트2/블루아카 등 미소녀 수집형 선호',
        'love': [
            'goddess of victory: nikke', 'nikke', 'genshin impact',
            'wuthering waves', 'myeongjo', 'brown dust 2', 'blue archive',
            'honkai', 'fate/grand order', 'fgo', 'umamusume', 'azur lane',
            'anime', 'waifu', 'gacha', 'visual novel', 'jrpg',
            'nudity', 'sexual content', 'action rpg', 'open world'
        ],
        'like': ['story rich', 'soundtrack', 'turn-based', 'adventure'],
        'dislike': ['western', 'military', 'sports', 'realistic', 'horror']
    },
    {
        'id': 'casual_puzzle_mom',
        'nickname': '캔디팡팡',
        'desc': '캔디크러시/피아노타일/로얄매치 등 가벼운 퍼즐 게임 선호',
        'love': [
            'candy crush saga', 'royal match', 'anipang', 'piano tiles',
            'gardenscapes', 'homescapes', 'angry birds', '2048',
            'fruit ninja', 'subway surfers', 'temple run',
            'puzzle', 'match 3', 'casual', 'relaxing',
            'rhythm', 'arcade', 'colorful', 'family friendly'
        ],
        'like': ['simulation', 'point and click', 'hidden object', 'cute'],
        'dislike': ['violent', 'gore', 'fps', 'action', 'hardcore', 'dark']
    },
    {
        'id': 'mobile_strategist',
        'nickname': '뇌지컬',
        'desc': '클래시오브클랜/클래시로얄/TFT 등 전략 게임 선호',
        'love': [
            'clash of clans', 'coc', 'clash royale', 'tft', 'teamfight tactics',
            'auto chess', 'bloons td', 'kingdom rush', 'marvel snap',
            'strategy', 'card battler', 'deck building', 'tower defense',
            'auto battler', 'pvp', 'rts', 'turn-based strategy'
        ],
        'like': ['management', 'simulation', 'board game', 'multiplayer'],
        'dislike': ['fps', 'action', 'horror', 'platformer', 'reflexes']
    },
    {
        'id': 'idle_grower',
        'nickname': '잠수부',
        'desc': '버섯커키우기/세븐나이츠키우기/메이플M 등 방치/성장형 선호',
        'love': [
            'mushroom hero', 'legend of mushroom', 'seven knights idle',
            'maplestory m', 'lineage m', 'afk arena', 'blade idle',
            'idle heroes', 'cookie run: kingdom',
            'idler', 'clicker', 'auto battler', 'incremental',
            'rpg', 'loot', 'casual', '2d'
        ],
        'like': ['pixel graphics', 'fantasy', 'management', 'simulation'],
        'dislike': ['difficult', 'precision platformer', 'puzzle', 'pvp']
    },
    {
        'id': 'social_deduction',
        'nickname': '범인은너',
        'desc': '마피아42/어몽어스/로블록스 등 소셜 파티게임 선호',
        'love': [
            'mafia42', 'among us', 'ice tag online', 'roblox',
            'goose goose duck', 'fall guys', 'stumble guys',
            'social deduction', 'party game', 'multiplayer', 'co-op',
            'funny', 'psychological', 'online co-op', 'casual'
        ],
        'like': ['survival', 'communication', 'strategy', 'minigames'],
        'dislike': ['singleplayer', 'rpg', 'grinding', 'visual novel']
    },
    {
        'id': 'creature_collector',
        'nickname': '포켓몬마스터',
        'desc': '포켓몬GO/쿠키런 등 몬스터 수집 및 캐주얼 게임 선호',
        'love': [
            'pokemon go', 'pokemon', 'cookie run', 'tamagotchi',
            'peridot', 'monster hunter now',
            'creature collector', 'monster tamer', 'open world',
            'exploration', 'cute', 'adventure', 'casual', 'turn-based combat'
        ],
        'like': ['rpg', 'simulation', 'anime', 'family friendly'],
        'dislike': ['fps', 'horror', 'gore', 'military', 'realistic']
    },
]

class Command(BaseCommand):
    help = '67명의 상세 페르소나 테스트 유저 생성 (각 500개 평가)'

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
                # 이미 온보딩이 완료된 유저라면 평가 로직 스킵 (빠른 재실행 지원)
                try:
                    onboarding = OnboardingStatus.objects.get(user=user)
                    if onboarding.status == 'completed':
                        self.stdout.write(f"[{i}/{len(USER_ARCHETYPES)}] {user.nickname}: 이미 온보딩 완료됨 (스킵)")
                        continue
                except OnboardingStatus.DoesNotExist:
                    pass

            # 평가 데이터 생성
            # 전체 게임 중 랜덤하게 500~600개를 선택하여 평가 (섞어서 다양성 확보)
            games_to_rate = random.sample(all_games, min(len(all_games), 600))
            
            created_count = self._create_ratings_for_user(user, games_to_rate, archetype)
            
            # 온보딩 완료 처리
            self._complete_onboarding(user, created_count)
            
            self.stdout.write(self.style.SUCCESS(
                f"[{i}/{len(USER_ARCHETYPES)}] {user.nickname}({username}): {created_count}개 평가 생성 완료 ({archetype['desc']})"
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
