"""
한국인이라면 해봤을 유명 게임들 DB 추가
Steam이 아닌 PC방/온라인 게임 중심

Usage:
    python manage.py add_korean_games
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from games.models import Game, Tag


# 한국에서 유행했던 유명 온라인/PC방 게임 목록
# RAWG에 없는 경우가 많으므로 수동 데이터
KOREAN_POPULAR_GAMES = [
    # === MMORPG / 온라인 RPG ===
    {
        'title': '메이플스토리 (MapleStory)',
        'genre': 'MMORPG, Side Scroller, 2D, Anime',
        'description': '넥슨에서 개발한 2D 횡스크롤 MMORPG. 2003년 출시 이후 한국을 대표하는 온라인게임으로 자리잡았다. 귀여운 도트 그래픽과 다양한 직업군, 보스레이드 컨텐츠가 특징.',
        'image_url': 'https://maplestory.nexon.com/media/nexon/maplestory/og_maplestory.jpg',
        'tags': ['mmorpg', '2d', 'side-scroller', 'anime', 'free-to-play', 'korean'],
    },
    {
        'title': '던전앤파이터 (Dungeon & Fighter)',
        'genre': 'Action RPG, Beat em up, 2D',
        'description': '네오플에서 개발한 2D 벨트스크롤 액션 RPG. 아케이드풍 타격감과 다양한 캐릭터가 매력. 중국에서 엄청난 인기를 얻어 세계 매출 1위 온라인게임 기록.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/9/97/Dungeon_Fighter_Online_cover.jpg',
        'tags': ['action-rpg', 'beat-em-up', '2d', 'hack-and-slash', 'free-to-play', 'korean'],
    },
    {
        'title': '라테일 (Latale)',
        'genre': 'MMORPG, Side Scroller, 2D, Anime',
        'description': '액토즈소프트에서 개발한 2D 횡스크롤 MMORPG. 메이플스토리와 유사하지만 더 화려한 스킬과 점핑 액션이 특징. "온라인 다락방"이라는 별명.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/6/69/La_Tale_logo.png',
        'tags': ['mmorpg', '2d', 'side-scroller', 'anime', 'free-to-play', 'korean'],
    },
    {
        'title': '로스트아크 (Lost Ark)',
        'genre': 'Action RPG, MMORPG, Isometric',
        'description': '스마일게이트에서 개발한 쿼터뷰 액션 MMORPG. 화려한 액션과 레이드, 시네마틱 스토리가 특징. 글로벌 서비스로 스팀 동시접속 세계 2위 기록.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/d/d0/Lost_Ark_cover.jpg',
        'steam_appid': 1599340,
        'tags': ['mmorpg', 'action-rpg', 'isometric', 'hack-and-slash', 'free-to-play', 'korean'],
    },
    {
        'title': '리니지 (Lineage)',
        'genre': 'MMORPG, Fantasy, PvP',
        'description': 'NC소프트에서 개발한 원조 MMORPG. 1998년 출시로 한국 온라인게임 역사의 시작. 피바람 전쟁, 성주 시스템 등 PvP 중심 컨텐츠가 특징.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/6/6e/Lineage_The_Blood_Pledge_logo.png',
        'tags': ['mmorpg', 'fantasy', 'pvp', 'medieval', 'free-to-play', 'korean'],
    },
    {
        'title': '리니지2 (Lineage II)',
        'genre': 'MMORPG, Fantasy, PvP, 3D',
        'description': 'NC소프트의 리니지 후속작. 언리얼 엔진 기반 3D 그래픽으로 혁신적인 비주얼. 공성전과 혈맹 시스템이 핵심.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/1/10/Lineage_II_logo.png',
        'tags': ['mmorpg', 'fantasy', 'pvp', '3d', 'free-to-play', 'korean'],
    },
    {
        'title': '마비노기 (Mabinogi)',
        'genre': 'MMORPG, Life Sim, Fantasy',
        'description': '넥슨/데브캣에서 개발한 힐링 온라인게임. 전투보다 생활 컨텐츠(작곡, 요리, 재봉 등)가 발달. 음유시인 시스템으로 게임 내 연주 가능.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/0/0a/Mabinogi_logo.png',
        'tags': ['mmorpg', 'life-sim', 'fantasy', 'music', 'free-to-play', 'korean'],
    },
    {
        'title': '검은사막 (Black Desert Online)',
        'genre': 'MMORPG, Action, Open World, Sandbox',
        'description': '펄어비스에서 개발한 오픈월드 액션 MMORPG. 논타겟팅 전투와 생활 컨텐츠, 캐릭터 커스터마이징이 강점. 화려한 그래픽으로 유명.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/0/07/Black_Desert_Online_cover.jpg',
        'steam_appid': 582660,
        'tags': ['mmorpg', 'action', 'open-world', 'sandbox', 'character-customization', 'korean'],
    },
    {
        'title': '아이온 (Aion)',
        'genre': 'MMORPG, Fantasy, PvP, Flying',
        'description': 'NC소프트의 비행 MMORPG. 하늘을 나는 전투가 특징. 천족과 마족의 대립 구도.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/f/f7/Aion_The_Tower_of_Eternity_logo.png',
        'tags': ['mmorpg', 'fantasy', 'pvp', 'flying', 'free-to-play', 'korean'],
    },
    {
        'title': '블레이드앤소울 (Blade & Soul)',
        'genre': 'MMORPG, Action, Martial Arts',
        'description': 'NC소프트의 무협 MMORPG. 김형태 작가의 캐릭터 디자인과 화려한 무술 액션이 특징. 비공술 등 독특한 시스템.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/c/c9/Blade_%26_Soul_logo.png',
        'tags': ['mmorpg', 'action', 'martial-arts', 'anime', 'free-to-play', 'korean'],
    },
    {
        'title': '마영전 (Vindictus / Mabinogi Heroes)',
        'genre': 'Action RPG, Hack and Slash, Co-op',
        'description': '넥슨/데브캣의 하드코어 액션 RPG. 소스 엔진 기반 물리 타격. 잔인한 피니시 무브와 격렬한 전투가 특징.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/9/93/Vindictus_logo.png',
        'steam_appid': 212160,
        'tags': ['action-rpg', 'hack-and-slash', 'co-op', 'difficult', 'free-to-play', 'korean'],
    },
    
    # === FPS / TPS ===
    {
        'title': '서든어택 (Sudden Attack)',
        'genre': 'FPS, Shooter, Multiplayer',
        'description': '한국의 국민 FPS. 게임하이에서 개발, 넥슨 서비스. 팀 데스매치, 폭파 미션 등 클래식 FPS 모드. PC방 점유율 1위를 오래 지켰던 게임.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/6/6e/Sudden_Attack_logo.png',
        'tags': ['fps', 'shooter', 'multiplayer', 'competitive', 'free-to-play', 'korean'],
    },
    {
        'title': '카운터 스트라이크 온라인 (Counter-Strike Online)',
        'genre': 'FPS, Shooter, Zombie, Multiplayer',
        'description': '넥슨이 서비스한 카스의 온라인화 버전. 좀비 모드, 다양한 무기 스킨 추가. 오리지널 카스에 한국식 컨텐츠 가미.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/archive/9/94/20220826012455%21Counter-Strike_Online_capsule.jpg',
        'tags': ['fps', 'shooter', 'zombie', 'multiplayer', 'free-to-play', 'korean'],
    },
    {
        'title': '스페셜포스 (Special Force)',
        'genre': 'FPS, Shooter, Tactical',
        'description': '드래곤플라이에서 개발한 밀리터리 FPS. 서든어택의 라이벌로 PC방에서 인기. 다양한 총기와 맵.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/3/37/Special_Force_logo.png',
        'tags': ['fps', 'shooter', 'tactical', 'military', 'multiplayer', 'free-to-play', 'korean'],
    },
    {
        'title': '배틀그라운드 (PUBG: BATTLEGROUNDS)',
        'genre': 'Battle Royale, Shooter, TPS',
        'description': '크래프톤(블루홀)에서 개발한 배틀로얄 게임. 100인 생존 슈터의 대중화를 이끈 게임. 전세계적 흥행.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/9/9f/Pubgbattlegrounds.png',
        'steam_appid': 578080,
        'tags': ['battle-royale', 'shooter', 'tps', 'survival', 'multiplayer', 'korean'],
    },
    {
        'title': '오버워치 (Overwatch 2)',
        'genre': 'FPS, Hero Shooter, Team-based',
        'description': '블리자드의 히어로 슈터. 한국에서 엄청난 인기를 끌며 e스포츠로 성장. 다양한 히어로와 팀 기반 전략.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/6/6a/Overwatch_2_full_logo.svg/1200px-Overwatch_2_full_logo.svg.png',
        'steam_appid': 2357570,
        'tags': ['fps', 'hero-shooter', 'team-based', 'competitive', 'multiplayer', 'esports'],
    },
    {
        'title': '발로란트 (VALORANT)',
        'genre': 'FPS, Tactical Shooter, Hero Shooter',
        'description': '라이엇게임즈의 택티컬 FPS. CS와 오버워치의 결합. 에이전트별 고유 능력과 정밀한 총격전.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/b/b7/Valorant_cover.jpg',
        'tags': ['fps', 'tactical-shooter', 'hero-shooter', 'competitive', 'esports', 'free-to-play'],
    },
    
    # === RTS / 전략 ===
    {
        'title': '스타크래프트 (StarCraft: Remastered)',
        'genre': 'RTS, Strategy, Sci-Fi',
        'description': '블리자드의 실시간 전략게임. 한국에서 e스포츠의 시작이 된 전설. 테란, 저그, 프로토스 3종족.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/9/93/StarCraft_Remastered_cover.jpg/220px-StarCraft_Remastered_cover.jpg',
        'steam_appid': None,  # Battle.net 전용
        'tags': ['rts', 'strategy', 'sci-fi', 'esports', 'competitive', 'military'],
    },
    {
        'title': '스타크래프트 II (StarCraft II)',
        'genre': 'RTS, Strategy, Sci-Fi',
        'description': '스타크래프트의 후속작. e스포츠와 협동 미션으로 인기. 화려한 그래픽과 전략적 깊이.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/2/20/StarCraft_II_-_Box_Art.jpg',
        'steam_appid': None,  # Battle.net 전용
        'tags': ['rts', 'strategy', 'sci-fi', 'esports', 'competitive', 'free-to-play'],
    },
    
    # === MOBA ===
    {
        'title': '리그 오브 레전드 (League of Legends)',
        'genre': 'MOBA, Strategy, Multiplayer',
        'description': '라이엇게임즈의 MOBA 게임. 전세계에서 가장 많이 플레이되는 게임 중 하나. 한국에서 압도적 1위 점유율.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/d/d8/League_of_Legends_2019_vector.svg',
        'tags': ['moba', 'strategy', 'team-based', 'competitive', 'esports', 'free-to-play'],
    },
    
    # === 레이싱 / 캐주얼 ===
    {
        'title': '크레이지레이싱 카트라이더 (KartRider)',
        'genre': 'Racing, Arcade, Multiplayer',
        'description': '넥슨의 캐주얼 레이싱 게임. 아이템전과 스피드전. 휴대폰 시절부터 PC방, 모바일까지 국민게임.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/8/86/KartRider_Drift_logo.png',
        'tags': ['racing', 'arcade', 'multiplayer', 'casual', 'fun', 'free-to-play', 'korean'],
    },
    {
        'title': '테일즈런너 (TalesRunner)',
        'genre': 'Racing, Platformer, Multiplayer',
        'description': '로커스에서 개발한 달리기 게임. 동화 속 세계관에서 점프와 대시, 아이템을 활용한 레이싱.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/3/3c/Tales_Runner_logo.png',
        'tags': ['racing', 'platformer', 'multiplayer', 'casual', 'anime', 'free-to-play', 'korean'],
    },
    {
        'title': '크레이지아케이드 (Crazy Arcade)',
        'genre': 'Puzzle, Action, Multiplayer',
        'description': '넥슨의 폭탄게임. 봄버맨 스타일에 아이템과 캐릭터 커스터마이징. 카트라이더와 함께 넥슨의 양대 캐주얼 게임.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/6/61/Crazy_Arcade_BnB_logo.png',
        'tags': ['puzzle', 'action', 'multiplayer', 'party-game', 'casual', 'free-to-play', 'korean'],
    },
    
    # === 스포츠 / 피파 ===
    {
        'title': 'FC 온라인 (FIFA Online 4 / FC Online)',
        'genre': 'Sports, Soccer, Multiplayer',
        'description': 'EA와 넥슨의 온라인 축구게임. PC방 점유율 최상위. 선수 뽑기와 스쿼드 꾸미, 온라인 대전이 핵심.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/8/8a/FC_Online_logo.svg/220px-FC_Online_logo.svg.png',
        'tags': ['sports', 'soccer', 'simulation', 'multiplayer', 'competitive', 'free-to-play'],
    },
    
    # === 디아블로 / 핵앤슬래시 ===
    {
        'title': '디아블로 II: 레저렉션 (Diablo II: Resurrected)',
        'genre': 'Action RPG, Hack and Slash, Dungeon Crawler',
        'description': '블리자드의 핵앤슬래시 RPG 리마스터. 한국 온라인게임 문화에 큰 영향. 아이템 파밍, 공포, 우울한 분위기.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/c/c1/Diablo_II_Resurrected_cover_art.png/220px-Diablo_II_Resurrected_cover_art.png',
        'steam_appid': None,  # Battle.net 전용
        'tags': ['action-rpg', 'hack-and-slash', 'dungeon-crawler', 'dark-fantasy', 'loot'],
    },
    {
        'title': '디아블로 III (Diablo III)',
        'genre': 'Action RPG, Hack and Slash',
        'description': '디아블로 시리즈 3편. 시즌제 운영과 그레이터 리프트 시스템.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/8/80/Diablo_III_cover.png',
        'steam_appid': None,  # Battle.net 전용
        'tags': ['action-rpg', 'hack-and-slash', 'dungeon-crawler', 'co-op', 'loot'],
    },
    {
        'title': '디아블로 IV (Diablo IV)',
        'genre': 'Action RPG, Hack and Slash, Open World',
        'description': '디아블로 시리즈 최신작. 오픈월드와 어두운 분위기 복귀. 시즌 업데이트.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/1/1b/Diablo_IV_cover_art.png',
        'steam_appid': 2344520,
        'tags': ['action-rpg', 'hack-and-slash', 'open-world', 'dark-fantasy', 'loot', 'co-op'],
    },
    
    # === 모바일 출신 / 서브컬쳐 ===
    {
        'title': '원신 (Genshin Impact)',
        'genre': 'Action RPG, Open World, Gacha',
        'description': '미호요의 오픈월드 액션 RPG. 젤다 풍 오픈월드에 가챠 시스템. 한국에서도 큰 인기.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/5/5d/Genshin_Impact_cover.jpg',
        'steam_appid': None,  # Epic/자체 런처
        'tags': ['action-rpg', 'open-world', 'gacha', 'anime', 'exploration', 'free-to-play'],
    },
    {
        'title': '블루아카이브 (Blue Archive)',
        'genre': 'RPG, Strategy, Gacha, Anime',
        'description': '넥슨게임즈의 미소녀 수집형 RPG. 학원물 세계관과 일러스트가 인기.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/7/7e/Blue_Archive_cover.jpg',
        'tags': ['rpg', 'strategy', 'gacha', 'anime', 'visual-novel', 'free-to-play', 'korean'],
    },
    
    # === 기타 클래식 ===
    {
        'title': '바람의나라 (Kingdom of the Winds)',
        'genre': 'MMORPG, 2D, Korean Mythology',
        'description': '넥슨의 원조 그래픽 MMORPG. 1996년 서비스 시작. 고구려 신화 기반.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/1/1f/Kingdom_of_the_Winds_logo.gif',
        'tags': ['mmorpg', '2d', 'korean', 'mythology', 'classic', 'free-to-play'],
    },
    {
        'title': '뮤 (MU Online)',
        'genre': 'MMORPG, 3D, Fantasy',
        'description': '웹젠의 3D MMORPG. 초기 3D 온라인게임 대표. 아이템 +13 강화 시스템의 원조.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/7/79/MU_Online_logo.png',
        'tags': ['mmorpg', '3d', 'fantasy', 'pvp', 'free-to-play', 'korean'],
    },
    {
        'title': '거상 (Gersang)',
        'genre': 'MMORPG, Trading, Economy',
        'description': '바람의나라와 함께 넥슨 초기 게임. 무역과 경제 시스템이 특징.',
        'image_url': '',  # 이미지 없음
        'tags': ['mmorpg', 'economy', 'trading', 'korean', 'classic', 'free-to-play'],
    },
    {
        'title': '그랜드체이스 (GrandChase)',
        'genre': 'Action RPG, Beat em up, 2D',
        'description': 'KOG에서 개발한 횡스크롤 액션 RPG. 던파와 유사한 벨트스크롤 액션. 엘소드의 전신.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/a/a7/GrandChase_logo.png',
        'tags': ['action-rpg', 'beat-em-up', '2d', 'anime', 'free-to-play', 'korean'],
    },
    {
        'title': '엘소드 (Elsword)',
        'genre': 'Action RPG, Beat em up, 2D, Anime',
        'description': 'KOG의 횡스크롤 액션 RPG. 그랜드체이스의 후속작. 화려한 스킬과 콤보.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/b/bc/Elsword_logo.png',
        'steam_appid': 0,  # Steam에도 있음
        'tags': ['action-rpg', 'beat-em-up', '2d', 'anime', 'free-to-play', 'korean'],
    },
    {
        'title': '메이플스토리 2 (MapleStory 2)',
        'genre': 'MMORPG, 3D, Casual, Building',
        'description': '메이플스토리의 3D 버전. 집꾸미기와 UGC 컨텐츠가 특징. 서비스 종료.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/c/c3/MapleStory_2_logo.png',
        'tags': ['mmorpg', '3d', 'casual', 'building', 'free-to-play', 'korean'],
    },
    
    # === 모바일 게임 ===
    {
        'title': '뱀파이어 서바이버즈 (Vampire Survivors)',
        'genre': 'Roguelike, Bullet Hell, Action',
        'description': '탕탕특공대 원조격 게임. 적을 피하며 무한 웨이브를 버티는 로그라이크.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/5/55/Vampire_Survivors_logo.png',
        'steam_appid': 1794680,
        'tags': ['roguelite', 'action', 'indie', 'bullet-hell', 'casual'],
    },
    {
        'title': '브롤스타즈 (Brawl Stars)',
        'genre': 'MOBA, Shooter, Multiplayer',
        'description': '수퍼셀의 3분 짧은 모바일 대전게임. 다양한 브롤러 캐릭터와 게임 모드.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/0/0e/Brawl_Stars_logo.png',
        'tags': ['moba', 'shooter', 'multiplayer', 'casual', 'team-based', 'free-to-play'],
    },
    {
        'title': '클래시 오브 클랜 (Clash of Clans)',
        'genre': 'Strategy, Base Building, Multiplayer',
        'description': '수퍼셀의 전략 모바일게임. 마을 건설과 클랜 전쟁.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/5/59/Clash_of_Clans_Logo.png',
        'tags': ['strategy', 'simulation', 'multiplayer', 'base-building', 'free-to-play'],
    },
    {
        'title': '클래시 로얄 (Clash Royale)',
        'genre': 'Strategy, Card Game, Tower Defense',
        'description': '수퍼셀의 실시간 전략 카드게임. 타워 디펜스와 카드 배틀의 결합.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/4/47/Clash_Royale_Logo.png/220px-Clash_Royale_Logo.png',
        'tags': ['strategy', 'card-game', 'tower-defense', 'pvp', 'competitive', 'free-to-play'],
    },
    {
        'title': '어몽어스 (Among Us)',
        'genre': 'Social Deduction, Party Game, Multiplayer',
        'description': '마피아 게임을 온라인으로. 크루원과 임포스터로 나뉘어 정체를 찾아내는 게임.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/9/9a/Among_Us_cover_art.png',
        'steam_appid': 945360,
        'tags': ['party-game', 'social-deduction', 'multiplayer', 'co-op', 'funny', 'casual'],
    },
    {
        'title': '폴가이즈 (Fall Guys)',
        'genre': 'Party Game, Battle Royale, Platformer',
        'description': '60명이 미니게임으로 경쟁하는 캐주얼 배틀로얄. 젤리빈 캐릭터.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/5/5e/Fall_Guys_cover.jpg/220px-Fall_Guys_cover.jpg',
        'steam_appid': 1097150,
        'tags': ['party-game', 'battle-royale', 'platformer', 'casual', 'funny', 'multiplayer'],
    },
    {
        'title': '로블록스 (Roblox)',
        'genre': 'Sandbox, Multiplayer, Creative',
        'description': '유저가 직접 게임을 만들고 플레이하는 플랫폼. 다양한 미니게임과 창작 컨텐츠.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/commons/3/3a/Roblox_player_icon_black.svg',
        'tags': ['sandbox', 'multiplayer', 'creative', 'casual', 'free-to-play', 'family-friendly'],
    },
    {
        'title': '마블 스냅 (Marvel Snap)',
        'genre': 'Card Game, Strategy, Marvel',
        'description': '마블 히어로 카드 배틀게임. 3분 빠른 대전.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/3/31/Marvel_Snap_logo.png',
        'steam_appid': 1997040,
        'tags': ['card-game', 'strategy', 'pvp', 'competitive', 'free-to-play'],
    },
    {
        'title': '쿠키런: 킹덤 (Cookie Run: Kingdom)',
        'genre': 'RPG, Simulation, Gacha',
        'description': '데브시스터즈의 쿠키런 시리즈 왕국 건설 버전. 귀여운 쿠키 수집과 왕국 꾸미기.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/7/7f/Cookie_Run_Kingdom_logo.png',
        'tags': ['rpg', 'simulation', 'gacha', 'cute', 'building', 'free-to-play', 'korean'],
    },
    {
        'title': '니케 (NIKKE: Goddess of Victory)',
        'genre': 'Shooter, RPG, Gacha, Anime',
        'description': '시프트업의 미소녀 슈팅 가챠게임. 화려한 일러스트와 슈팅 액션.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/3/30/Goddess_of_Victory_Nikke_Logo.png',
        'tags': ['shooter', 'rpg', 'gacha', 'anime', 'action', 'free-to-play', 'korean'],
    },
    {
        'title': '명일방주 (Arknights)',
        'genre': 'Tower Defense, Strategy, Gacha',
        'description': '하이퍼그리프의 타워 디펜스 가챠게임. 전략적인 배치와 캐릭터 수집.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/c/c1/Arknights_logo.png',
        'tags': ['tower-defense', 'strategy', 'gacha', 'anime', 'tactical', 'free-to-play'],
    },
    {
        'title': '붕괴: 스타레일 (Honkai: Star Rail)',
        'genre': 'Turn-based RPG, Gacha, Sci-Fi',
        'description': '호요버스의 턴제 RPG. 우주를 배경으로 한 스토리와 캐릭터 수집.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/0/00/Honkai_Star_Rail_cover.jpg',
        'tags': ['turn-based', 'rpg', 'gacha', 'anime', 'sci-fi', 'story-rich', 'free-to-play'],
    },
    {
        'title': '명조: 워더링 웨이브 (Wuthering Waves)',
        'genre': 'Action RPG, Open World, Gacha',
        'description': '쿠로게임즈의 오픈월드 액션 RPG. 원신과 경쟁하는 신작.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/9/9d/Wuthering_Waves_logo.png',
        'tags': ['action-rpg', 'open-world', 'gacha', 'anime', 'exploration', 'free-to-play'],
    },
    {
        'title': '우마무스메 (Umamusume: Pretty Derby)',
        'genre': 'Simulation, Racing, Gacha, Anime',
        'description': '말을 의인화한 레이싱 육성 시뮬레이션. 일본에서 큰 인기.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/e/e1/Uma_Musume_Pretty_Derby_Logo.png',
        'tags': ['simulation', 'racing', 'gacha', 'anime', 'cute', 'free-to-play'],
    },
    {
        'title': '페그오 (Fate/Grand Order)',
        'genre': 'Turn-based RPG, Gacha, Visual Novel',
        'description': '페이트 시리즈의 모바일 RPG. 역사 영웅들을 소환하는 가챠 게임.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/f/f7/Fate_Grand_Order_logo.png',
        'tags': ['turn-based', 'rpg', 'gacha', 'anime', 'visual-novel', 'story-rich', 'free-to-play'],
    },
    {
        'title': '리그 오브 레전드: 와일드 리프트 (LoL: Wild Rift)',
        'genre': 'MOBA, Strategy, Multiplayer',
        'description': '롤의 모바일 버전. 모바일에 최적화된 조작과 빠른 게임 시간.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/c/c5/League_of_Legends_Wild_Rift.png',
        'tags': ['moba', 'strategy', 'team-based', 'competitive', 'esports', 'free-to-play'],
    },
    {
        'title': '팀파이트 택틱스 (Teamfight Tactics)',
        'genre': 'Auto Battler, Strategy, Multiplayer',
        'description': '롤 세계관의 오토배틀러. 챔피언 조합과 시너지가 핵심.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/7/73/Teamfight_Tactics_logo.png',
        'tags': ['auto-battler', 'strategy', 'pvp', 'tactical', 'free-to-play'],
    },
    
    # === 닌텐도 1세대 클래식 ===
    {
        'title': '슈퍼 마리오 시리즈 (Super Mario Bros.)',
        'genre': 'Platformer, Action, Adventure',
        'description': '닌텐도의 대표 프랜차이즈. 배관공 마리오의 모험을 그린 플랫포머의 교과서.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/a/a9/MarioNSMBUDeluxe.png',
        'tags': ['platformer', 'action', 'adventure', 'family-friendly', 'nintendo', 'classic'],
    },
    {
        'title': '슈퍼 마리오 오디세이 (Super Mario Odyssey)',
        'genre': 'Platformer, Action, Open World',
        'description': '닌텐도 스위치의 3D 마리오. 모자를 던져 적을 조종하는 메카닉.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/8/8d/Super_Mario_Odyssey.jpg',
        'tags': ['platformer', 'action', 'open-world', 'exploration', 'nintendo', 'family-friendly'],
    },
    {
        'title': '슈퍼 마리오 갤럭시 (Super Mario Galaxy)',
        'genre': 'Platformer, Action, Adventure',
        'description': 'Wii의 3D 마리오. 중력을 활용한 독특한 스테이지와 우주 탐험.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/7/76/SuperMarioGalaxy.jpg',
        'tags': ['platformer', 'action', 'adventure', 'nintendo', 'family-friendly', 'exploration'],
    },
    {
        'title': '마리오 카트 8 디럭스 (Mario Kart 8 Deluxe)',
        'genre': 'Racing, Arcade, Multiplayer',
        'description': '닌텐도 레이싱 게임의 결정판. 아이템전과 코스가 매력.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/b/b5/MarioKart8Deluxe.jpg',
        'tags': ['racing', 'arcade', 'multiplayer', 'party-game', 'family-friendly', 'nintendo'],
    },
    {
        'title': '마리오 파티 슈퍼스타즈 (Mario Party Superstars)',
        'genre': 'Party Game, Minigames, Multiplayer',
        'description': '닌텐도 파티게임 시리즈. 보드게임과 미니게임의 조합.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/1/1e/Mario_Party_Superstars.jpg',
        'tags': ['party-game', 'minigames', 'multiplayer', 'casual', 'family-friendly', 'nintendo'],
    },
    {
        'title': '슈퍼 스매시 브라더스 얼티밋 (Super Smash Bros. Ultimate)',
        'genre': 'Fighting, Crossover, Multiplayer',
        'description': '닌텐도 올스타 격투게임. 마리오, 링크, 포켓몬 등이 한 자리에.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/5/50/Super_Smash_Bros._Ultimate.jpg',
        'tags': ['fighting', 'action', 'multiplayer', 'party-game', 'crossover', 'nintendo'],
    },
    
    # === 젤다의 전설 시리즈 ===
    {
        'title': '젤다의 전설: 브레스 오브 더 와일드 (The Legend of Zelda: Breath of the Wild)',
        'genre': 'Action-Adventure, Open World, RPG',
        'description': '오픈월드 액션 어드벤처의 혁명. 자유로운 탐험과 물리 기반 퍼즐.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/c/c6/The_Legend_of_Zelda_Breath_of_the_Wild.jpg',
        'tags': ['action-adventure', 'open-world', 'exploration', 'rpg', 'nintendo', 'masterpiece'],
    },
    {
        'title': '젤다의 전설: 티어스 오브 더 킹덤 (The Legend of Zelda: Tears of the Kingdom)',
        'genre': 'Action-Adventure, Open World, RPG',
        'description': '브레스 오브 더 와일드의 후속작. 울트라핸드와 하늘섬이 추가.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/f/fb/The_Legend_of_Zelda_Tears_of_the_Kingdom_cover.jpg',
        'tags': ['action-adventure', 'open-world', 'exploration', 'rpg', 'nintendo', 'masterpiece', 'crafting'],
    },
    {
        'title': '젤다의 전설: 시간의 오카리나 (The Legend of Zelda: Ocarina of Time)',
        'genre': 'Action-Adventure, RPG',
        'description': 'N64 시대 3D 어드벤처의 걸작. 시간 여행과 던전 탐험.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/5/57/The_Legend_of_Zelda_Ocarina_of_Time.jpg',
        'tags': ['action-adventure', 'rpg', 'exploration', 'puzzle', 'nintendo', 'classic', 'masterpiece'],
    },
    {
        'title': '젤다의 전설: 꿈꾸는 섬 (The Legend of Zelda: Link\'s Awakening)',
        'genre': 'Action-Adventure, Puzzle',
        'description': '게임보이 클래식의 리메이크. 귀여운 그래픽과 던전 퍼즐.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/d/da/Link%27s_Awakening_Remake_Boxart.png',
        'tags': ['action-adventure', 'puzzle', 'cute', 'nintendo', 'classic'],
    },
    
    # === 포켓몬 시리즈 ===
    {
        'title': '포켓몬스터 스칼렛/바이올렛 (Pokémon Scarlet/Violet)',
        'genre': 'RPG, Monster Collection, Open World',
        'description': '최초의 오픈월드 포켓몬. 스페인 풍 지역을 탐험하며 포켓몬 수집.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/a/a7/Pok%C3%A9mon_Scarlet_and_Violet.png',
        'tags': ['rpg', 'monster-tamer', 'open-world', 'turn-based', 'nintendo', 'adventure'],
    },
    {
        'title': '포켓몬스터 소드/실드 (Pokémon Sword/Shield)',
        'genre': 'RPG, Monster Collection, Adventure',
        'description': '스위치 첫 본편 포켓몬. 와일드 에리어와 다이맥스 배틀.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/3/3a/Pok%C3%A9mon_Sword_and_Shield.png',
        'tags': ['rpg', 'monster-tamer', 'adventure', 'turn-based', 'nintendo'],
    },
    {
        'title': '포켓몬 레전드 아르세우스 (Pokémon Legends: Arceus)',
        'genre': 'Action RPG, Monster Collection, Open World',
        'description': '과거 시대 포켓몬 세계. 액션 기반 야생 포켓몬 포획.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/9/9e/Pokemon_Legends_Arceus_cover.jpg',
        'tags': ['action-rpg', 'monster-tamer', 'open-world', 'exploration', 'nintendo'],
    },
    {
        'title': '포켓몬스터 다이아몬드/펄 리메이크 (Pokémon Brilliant Diamond/Shining Pearl)',
        'genre': 'RPG, Monster Collection',
        'description': '4세대 포켓몬의 스위치 리메이크. 신오지방 모험.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/b/b5/Pokémon_Brilliant_Diamond_and_Shining_Pearl.png',
        'tags': ['rpg', 'monster-tamer', 'adventure', 'turn-based', 'nintendo', 'classic'],
    },
    {
        'title': '포켓몬스터 레츠고 피카츄/이브이 (Pokémon Let\'s Go)',
        'genre': 'RPG, Monster Collection, Casual',
        'description': '포켓몬 GO 스타일의 본편 게임. 모션 컨트롤 포획.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/4/4a/Pok%C3%A9mon_Let%27s_Go%2C_Pikachu%21_and_Pok%C3%A9mon_Let%27s_Go%2C_Eevee%21.png',
        'tags': ['rpg', 'monster-tamer', 'casual', 'cute', 'nintendo', 'family-friendly'],
    },
    
    # === 동물의 숲 시리즈 ===
    {
        'title': '모여봐요 동물의 숲 (Animal Crossing: New Horizons)',
        'genre': 'Life Simulation, Sandbox, Relaxing',
        'description': '무인도에서 시작하는 힐링 라이프 시뮬레이션. 코로나 시대 대유행.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/1/1f/Animal_Crossing_New_Horizons.jpg',
        'tags': ['life-sim', 'sandbox', 'relaxing', 'casual', 'cute', 'nintendo', 'building'],
    },
    {
        'title': '놀러오세요 동물의 숲 (Animal Crossing: Wild World)',
        'genre': 'Life Simulation, Relaxing',
        'description': 'DS용 동물의 숲. 휴대용으로 즐기는 마을 생활 시뮬레이션.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/f/fb/Animal_Crossing_Wild_World.jpg',
        'tags': ['life-sim', 'relaxing', 'casual', 'cute', 'nintendo', 'classic'],
    },
    
    # === 스플래툰 시리즈 ===
    {
        'title': '스플래툰 3 (Splatoon 3)',
        'genre': 'TPS, Shooter, Multiplayer',
        'description': '잉크를 뿌려 영역을 확보하는 슈터. 유니크한 게임성과 스타일리시한 디자인.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/6/60/Splatoon_3_box_art.jpg',
        'tags': ['shooter', 'tps', 'multiplayer', 'team-based', 'competitive', 'nintendo', 'colorful'],
    },
    {
        'title': '스플래툰 2 (Splatoon 2)',
        'genre': 'TPS, Shooter, Multiplayer',
        'description': '스위치용 스플래툰. 연어런과 오카스퀘어.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/d/d0/Splatoon_2_NA_box.jpg',
        'tags': ['shooter', 'tps', 'multiplayer', 'team-based', 'competitive', 'nintendo'],
    },
    
    # === 커비 시리즈 ===
    {
        'title': '별의 커비: 디스커버리 (Kirby and the Forgotten Land)',
        'genre': 'Platformer, Action, Adventure',
        'description': '커비 시리즈 첫 3D 플랫포머. 머금기와 입체운동 능력.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/d/dc/Kirby_and_the_Forgotten_Land_box_art.jpg',
        'tags': ['platformer', 'action', 'adventure', 'cute', 'nintendo', 'family-friendly'],
    },
    {
        'title': '별의 커비 스타 얼라이즈 (Kirby Star Allies)',
        'genre': 'Platformer, Action, Co-op',
        'description': '스위치용 커비. 적을 동료로 만드는 시스템.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/8/8c/Kirby_Star_Allies.jpg',
        'tags': ['platformer', 'action', 'co-op', 'cute', 'nintendo', 'family-friendly'],
    },
    
    # === 피트니스/리듬/파티 게임 ===
    {
        'title': '링피트 어드벤처 (Ring Fit Adventure)',
        'genre': 'Fitness, RPG, Adventure',
        'description': '링콘 컨트롤러로 운동하며 모험하는 피트니스 게임.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/02/Ring_Fit_Adventure_Key_Art.jpg/220px-Ring_Fit_Adventure_Key_Art.jpg',
        'tags': ['fitness', 'rpg', 'adventure', 'casual', 'nintendo', 'family-friendly'],
    },
    {
        'title': '저스트 댄스 2024 (Just Dance 2024)',
        'genre': 'Rhythm, Dance, Music',
        'description': '유비소프트의 댄스 게임. K-POP 포함 다양한 곡 수록.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/6/69/Just_Dance_2024_Cover.jpg',
        'tags': ['rhythm', 'music', 'fitness', 'party-game', 'casual', 'family-friendly'],
    },
    {
        'title': '리듬 세상 (Rhythm Heaven)',
        'genre': 'Rhythm, Music, Minigames',
        'description': '닌텐도의 리듬 게임. 기발한 미니게임과 중독성 있는 음악.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/7/79/Rhythm_Heaven_cover.jpg',
        'tags': ['rhythm', 'music', 'minigames', 'casual', 'nintendo', 'funny'],
    },
    {
        'title': 'Wii 스포츠 (Wii Sports)',
        'genre': 'Sports, Casual, Multiplayer',
        'description': 'Wii 시대의 혁명. 모션 컨트롤로 즐기는 테니스, 야구, 볼링 등.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/e/e0/Wii_Sports_Europe.jpg',
        'tags': ['sports', 'casual', 'multiplayer', 'party-game', 'nintendo', 'family-friendly', 'classic'],
    },
    {
        'title': 'Nintendo Switch Sports',
        'genre': 'Sports, Casual, Multiplayer',
        'description': 'Wii 스포츠의 스위치 버전. 배드민턴, 축구 등 추가.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/d/d2/Nintendo_Switch_Sports_Cover.jpg',
        'tags': ['sports', 'casual', 'multiplayer', 'party-game', 'nintendo', 'family-friendly'],
    },
    
    # === 레이튼/미스터리 게임 ===
    {
        'title': '레이튼 교수 시리즈 (Professor Layton)',
        'genre': 'Puzzle, Adventure, Mystery',
        'description': '레이튼 교수의 퍼즐 어드벤처. 수백 개의 두뇌 퍼즐과 미스터리 스토리.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/b/b5/Professor_Layton_and_the_Curious_Village.jpg',
        'tags': ['puzzle', 'adventure', 'mystery', 'story-rich', 'nintendo', 'casual'],
    },
    {
        'title': '역전재판 시리즈 (Ace Attorney)',
        'genre': 'Visual Novel, Adventure, Mystery',
        'description': '법정 어드벤처 게임. 증거를 모아 범인을 밝혀내는 스토리.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/a/a3/Ace_Attorney_Trilogy.jpg',
        'steam_appid': 787480,
        'tags': ['visual-novel', 'adventure', 'mystery', 'story-rich', 'puzzle'],
    },
    
    # === 기타 닌텐도 명작 ===
    {
        'title': '파이어 엠블렘: 풍화설월 (Fire Emblem: Three Houses)',
        'genre': 'Tactical RPG, Strategy, Story Rich',
        'description': '닌텐도 택티컬 RPG. 학원 파트와 전쟁 파트로 구성.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/1/1f/Fire_Emblem_Three_Houses.jpg',
        'tags': ['tactical-rpg', 'strategy', 'story-rich', 'anime', 'turn-based', 'nintendo'],
    },
    {
        'title': '파이어 엠블렘 인게이지 (Fire Emblem Engage)',
        'genre': 'Tactical RPG, Strategy',
        'description': '역대 FE 영웅들이 등장하는 신작. 전략적 깊이와 팬서비스.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/f/f2/Fire_Emblem_Engage_cover.jpg',
        'tags': ['tactical-rpg', 'strategy', 'anime', 'turn-based', 'nintendo'],
    },
    {
        'title': '제노블레이드 크로니클스 3 (Xenoblade Chronicles 3)',
        'genre': 'JRPG, Action RPG, Open World',
        'description': '모노리스 소프트의 대작 JRPG. 방대한 월드와 스토리.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/e/e4/Xenoblade_Chronicles_3_cover.jpg',
        'tags': ['jrpg', 'action-rpg', 'open-world', 'story-rich', 'nintendo'],
    },
    {
        'title': '메트로이드 드레드 (Metroid Dread)',
        'genre': 'Metroidvania, Action, Exploration',
        'description': '19년 만의 메트로이드 2D 신작. 긴장감 넘치는 탐험.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/0/0f/Metroid_Dread_key_visual.jpg',
        'tags': ['metroidvania', 'action', 'exploration', 'sci-fi', 'nintendo'],
    },
    {
        'title': '동키콩 컨트리 리턴즈 (Donkey Kong Country Returns)',
        'genre': 'Platformer, Action, Co-op',
        'description': '레트로 스튜디오의 동키콩 부활작. 하드코어 플랫포머.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/2/20/Donkey_Kong_Country_Returns_Cover.png',
        'tags': ['platformer', 'action', 'co-op', 'difficult', 'nintendo', 'classic'],
    },
    {
        'title': '요시 시리즈 (Yoshi\'s Crafted World)',
        'genre': 'Platformer, Puzzle, Cute',
        'description': '공예 스타일의 요시 게임. 귀엽고 창의적인 스테이지.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/9/91/Yoshis_Crafted_World.jpg',
        'tags': ['platformer', 'puzzle', 'cute', 'casual', 'nintendo', 'family-friendly'],
    },
    {
        'title': '피크민 4 (Pikmin 4)',
        'genre': 'Strategy, Puzzle, Adventure',
        'description': '미야모토의 피크민 시리즈. 작은 생물들을 지휘해 탐험.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/2/2f/Pikmin_4_cover_art.jpg',
        'tags': ['strategy', 'puzzle', 'adventure', 'cute', 'nintendo'],
    },
    {
        'title': '루이지 맨션 3 (Luigi\'s Mansion 3)',
        'genre': 'Action-Adventure, Puzzle, Horror',
        'description': '루이지의 유령 저택 탐험. 코믹 호러 어드벤처.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/thumb/a/a0/Luigi%27s_Mansion_3_cover_art.jpg/220px-Luigi%27s_Mansion_3_cover_art.jpg',
        'tags': ['action-adventure', 'puzzle', 'horror', 'funny', 'nintendo', 'co-op'],
    },
    {
        'title': '베이오네타 3 (Bayonetta 3)',
        'genre': 'Action, Hack and Slash',
        'description': '플래티넘 게임즈의 스타일리시 액션. 화려한 액션과 성인 유머.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/0/0e/Bayonetta_3.jpg',
        'tags': ['action', 'hack-and-slash', 'action-adventure', 'female-protagonist', 'nintendo'],
    },
    {
        'title': '테트리스 99 (Tetris 99)',
        'genre': 'Puzzle, Battle Royale, Multiplayer',
        'description': '테트리스 배틀로얄. 99명 중 최후의 1인.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/4/4e/Tetris_99_cover_art.jpg',
        'tags': ['puzzle', 'battle-royale', 'multiplayer', 'competitive', 'nintendo', 'free-to-play'],
    },
]



class Command(BaseCommand):
    help = '한국에서 유행했던 유명 온라인/PC방 게임들을 DB에 추가합니다'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='기존 한국 게임 데이터 삭제 후 재생성',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("한국 유명 게임 데이터 추가 시작...")
        
        # 태그 생성 먼저
        self._ensure_tags()
        
        created_count = 0
        updated_count = 0
        
        for game_data in KOREAN_POPULAR_GAMES:
            title = game_data['title']
            
            # 기존 게임 찾기 (제목으로)
            # 한글 부분만 또는 영문 부분만으로도 검색
            title_parts = title.split(' (')
            korean_title = title_parts[0].strip()
            english_title = title_parts[1].rstrip(')').strip() if len(title_parts) > 1 else None
            
            existing = Game.objects.filter(title__icontains=korean_title).first()
            if not existing and english_title:
                existing = Game.objects.filter(title__icontains=english_title).first()
            
            if existing:
                if options['delete']:
                    existing.delete()
                    self.stdout.write(f"  삭제: {title}")
                else:
                    # 업데이트만
                    existing.description = game_data.get('description', existing.description)
                    existing.genre = game_data.get('genre', existing.genre)
                    existing.save()
                    updated_count += 1
                    self.stdout.write(f"  업데이트: {title}")
                    continue
            
            # 새 게임 생성
            game = Game.objects.create(
                title=title,
                genre=game_data.get('genre', ''),
                description=game_data.get('description', ''),
                image_url=game_data.get('image_url', ''),
                steam_appid=game_data.get('steam_appid'),
                rawg_id=None,  # RAWG에 없는 게임
            )
            
            # 태그 연결
            tag_slugs = game_data.get('tags', [])
            for slug in tag_slugs:
                tag = Tag.objects.filter(slug=slug).first()
                if tag:
                    game.tags.add(tag)
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"  추가: {title}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"\n완료! 생성: {created_count}개, 업데이트: {updated_count}개"
        ))
    
    def _ensure_tags(self):
        """필요한 태그가 없으면 생성"""
        required_tags = [
            # 기존 태그
            ('korean', '한국게임', 'feature'),
            ('free-to-play', 'F2P', 'feature'),
            ('mmorpg', 'MMORPG', 'genre'),
            ('fps', 'FPS', 'genre'),
            ('moba', 'MOBA', 'genre'),
            ('rts', 'RTS', 'genre'),
            ('action-rpg', '액션 RPG', 'genre'),
            ('beat-em-up', '벨트스크롤', 'genre'),
            ('racing', '레이싱', 'genre'),
            ('sports', '스포츠', 'genre'),
            ('battle-royale', '배틀로얄', 'genre'),
            ('gacha', '가챠', 'feature'),
            ('esports', 'e스포츠', 'feature'),
            ('competitive', '경쟁', 'feature'),
            ('team-based', '팀 기반', 'feature'),
            ('side-scroller', '횡스크롤', 'genre'),
            ('hack-and-slash', '핵앤슬래시', 'genre'),
            ('dungeon-crawler', '던전 크롤러', 'genre'),
            ('martial-arts', '무협', 'theme'),
            ('anime', '애니메이션', 'theme'),
            ('life-sim', '생활 시뮬', 'genre'),
            ('open-world', '오픈월드', 'feature'),
            ('sandbox', '샌드박스', 'feature'),
            ('pvp', 'PvP', 'feature'),
            ('co-op', '협동', 'feature'),
            ('loot', '루팅', 'feature'),
            
            # 닌텐도 태그
            ('nintendo', '닌텐도', 'platform'),
            ('platformer', '플랫포머', 'genre'),
            ('party-game', '파티게임', 'genre'),
            ('family-friendly', '전연령', 'feature'),
            ('cute', '귀여운', 'theme'),
            ('classic', '클래식', 'feature'),
            ('masterpiece', '명작', 'feature'),
            ('exploration', '탐험', 'feature'),
            ('monster-tamer', '몬스터 수집', 'genre'),
            ('turn-based', '턴제', 'genre'),
            ('tactical-rpg', '택티컬 RPG', 'genre'),
            ('jrpg', 'JRPG', 'genre'),
            ('metroidvania', '메트로배니아', 'genre'),
            ('fighting', '격투', 'genre'),
            ('crossover', '크로스오버', 'theme'),
            ('colorful', '컬러풀', 'theme'),
            ('relaxing', '힐링', 'feature'),
            ('building', '건설', 'feature'),
            ('minigames', '미니게임', 'genre'),
            ('fitness', '피트니스', 'genre'),
            ('rhythm', '리듬', 'genre'),
            ('music', '음악', 'theme'),
            
            # 모바일 게임 태그
            ('tower-defense', '타워 디펜스', 'genre'),
            ('auto-battler', '오토배틀러', 'genre'),
            ('card-game', '카드게임', 'genre'),
            ('social-deduction', '소셜 추리', 'genre'),
            ('roguelite', '로그라이트', 'genre'),
            ('bullet-hell', '탄막', 'genre'),
            ('base-building', '기지건설', 'genre'),
            ('creative', '창작', 'feature'),
            ('funny', '웃긴', 'feature'),
            ('tps', 'TPS', 'genre'),
            ('shooter', '슈터', 'genre'),
            ('tactical', '전술', 'feature'),
            
            # 기타 태그
            ('mystery', '미스터리', 'theme'),
            ('story-rich', '스토리', 'feature'),
            ('sci-fi', 'SF', 'theme'),
            ('horror', '호러', 'theme'),
            ('female-protagonist', '여성 주인공', 'feature'),
            ('visual-novel', '비주얼 노벨', 'genre'),
            ('crafting', '크래프팅', 'feature'),
        ]
        
        for slug, name, tag_type in required_tags:
            Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'tag_type': tag_type}
            )

