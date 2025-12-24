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
        'image_url': '/img/maple.jpg',
        'skip_rawg': True,
        'tags': ['mmorpg', '2d', 'side-scroller', 'anime', 'free-to-play', 'korean'],
    },
    {
        'title': '던전앤파이터 (Dungeon & Fighter)',
        'genre': 'Action RPG, Beat em up, 2D',
        'description': '네오플에서 개발한 2D 벨트스크롤 액션 RPG. 아케이드풍 타격감과 다양한 캐릭터가 매력. 중국에서 엄청난 인기를 얻어 세계 매출 1위 온라인게임 기록.',
        'image_url': '/img/dnf.jpg',
        'skip_rawg': True,
        'tags': ['action-rpg', 'beat-em-up', '2d', 'hack-and-slash', 'free-to-play', 'korean'],
    },
    {
        'title': '라테일 (Latale)',
        'genre': 'MMORPG, Side Scroller, 2D, Anime',
        'description': '액토즈소프트에서 개발한 2D 횡스크롤 MMORPG. 메이플스토리와 유사하지만 더 화려한 스킬과 점핑 액션이 특징. "온라인 다락방"이라는 별명.',
        'image_url': '/img/latale.jpg',
        'skip_rawg': True,
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
        'image_url': '/img/lineage.jpg',
        'skip_rawg': True,
        'tags': ['mmorpg', 'fantasy', 'pvp', 'medieval', 'free-to-play', 'korean'],
    },
    {
        'title': '리니지2 (Lineage II)',
        'genre': 'MMORPG, Fantasy, PvP, 3D',
        'description': 'NC소프트의 리니지 후속작. 언리얼 엔진 기반 3D 그래픽으로 혁신적인 비주얼. 공성전과 혈맹 시스템이 핵심.',
        'image_url': '/img/lineage2.jpg',
        'skip_rawg': True,
        'tags': ['mmorpg', 'fantasy', 'pvp', '3d', 'free-to-play', 'korean'],
    },
    {
        'title': '마비노기 (Mabinogi)',
        'genre': 'MMORPG, Life Sim, Fantasy',
        'description': '넥슨/데브캣에서 개발한 힐링 온라인게임. 전투보다 생활 컨텐츠(작곡, 요리, 재봉 등)가 발달. 음유시인 시스템으로 게임 내 연주 가능.',
        'image_url': '/img/mabinogi.jpg',
        'skip_rawg': True,
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
        'image_url': '/img/aion.jpg',
        'skip_rawg': True,
        'tags': ['mmorpg', 'fantasy', 'pvp', 'flying', 'free-to-play', 'korean'],
    },
    {
        'title': '블레이드앤소울 (Blade & Soul)',
        'genre': 'MMORPG, Action, Martial Arts',
        'description': 'NC소프트의 무협 MMORPG. 김형태 작가의 캐릭터 디자인과 화려한 무술 액션이 특징. 비공술 등 독특한 시스템.',
        'image_url': '/img/blade_and_soul.png',  # 수동 이미지 필요 (로고가 아닌 게임 이미지)
        'skip_rawg': True,  # 정확한 이미지 확보
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
        'image_url': '/img/sudden_attack.jpg',  # 수동 이미지 필요
        'skip_rawg': True,  # 한국 고유 게임
        'tags': ['fps', 'shooter', 'multiplayer', 'competitive', 'free-to-play', 'korean'],
    },
    {
        'title': '카운터 스트라이크 온라인 (Counter-Strike Online)',
        'genre': 'FPS, Shooter, Zombie, Multiplayer',
        'description': '넥슨이 서비스한 카스의 온라인화 버전. 좀비 모드, 다양한 무기 스킨 추가. 오리지널 카스에 한국식 컨텐츠 가미.',
        'image_url': '/img/cso.jpg',  # 수동 이미지 필요 (CS 시리즈와 구분)
        'skip_rawg': True,  # RAWG에서 다른 CS 게임과 혼동됨
        'tags': ['fps', 'shooter', 'zombie', 'multiplayer', 'free-to-play', 'korean'],
    },
    {
        'title': '스페셜포스 (Special Force)',
        'genre': 'FPS, Shooter, Tactical',
        'description': '드래곤플라이에서 개발한 밀리터리 FPS. 서든어택의 라이벌로 PC방에서 인기. 다양한 총기와 맵.',
        'image_url': '/img/SpecialForce.jpg',
        'skip_rawg': True,
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
        'image_url': '/img/valorant.jpg',
        'skip_rawg': True,
        'tags': ['fps', 'tactical-shooter', 'hero-shooter', 'competitive', 'esports', 'free-to-play'],
    },
    
    # === RTS / 전략 ===
    {
        'title': '스타크래프트 (StarCraft: Remastered)',
        'genre': 'RTS, Strategy, Sci-Fi',
        'description': '블리자드의 실시간 전략게임. 한국에서 e스포츠의 시작이 된 전설. 테란, 저그, 프로토스 3종족.',
        'image_url': '/img/StarCraft.jpg',
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
        'image_url': '/img/lol.jpg',
        'skip_rawg': True,
        'tags': ['moba', 'strategy', 'team-based', 'competitive', 'esports', 'free-to-play'],
    },
    
    # === 레이싱 / 캐주얼 ===
    {
        'title': '크레이지레이싱 카트라이더 (KartRider)',
        'genre': 'Racing, Arcade, Multiplayer',
        'description': '넥슨의 캐주얼 레이싱 게임. 아이템전과 스피드전. 휴대폰 시절부터 PC방, 모바일까지 국민게임.',
        'image_url': '/img/Kartrider.jpg',
        'skip_rawg': True,
        'tags': ['racing', 'arcade', 'multiplayer', 'casual', 'fun', 'free-to-play', 'korean'],
    },
    {
        'title': '테일즈런너 (TalesRunner)',
        'genre': 'Racing, Platformer, Multiplayer',
        'description': '로커스에서 개발한 달리기 게임. 동화 속 세계관에서 점프와 대시, 아이템을 활용한 레이싱.',
        'image_url': '/img/Talesrunner.jpg',
        'skip_rawg': True,
        'tags': ['racing', 'platformer', 'multiplayer', 'casual', 'anime', 'free-to-play', 'korean'],
    },
    {
        'title': '크레이지아케이드 (Crazy Arcade)',
        'genre': 'Puzzle, Action, Multiplayer',
        'description': '넥슨의 폭탄게임. 봄버맨 스타일에 아이템과 캐릭터 커스터마이징. 카트라이더와 함께 넥슨의 양대 캐주얼 게임.',
        'image_url': '/img/crazy_arcade.jpg',  # 수동 이미지 필요
        'skip_rawg': True,  # 한국 고유 게임
        'tags': ['puzzle', 'action', 'multiplayer', 'party-game', 'casual', 'free-to-play', 'korean'],
    },
    
    # === 스포츠 / 피파 ===
    {
        'title': 'FC 온라인 (FC Online)',
        'genre': 'Sports, Soccer, Multiplayer',
        'description': 'EA와 넥슨의 온라인 축구게임. PC방 점유율 최상위. 선수 뽑기와 스쿼드 꾸미기, 온라인 대전이 핵심.',
        'image_url': '/img/fc_online.jpg',  # 수동 이미지 필요 (로고가 아닌 게임 이미지)
        'skip_rawg': True,  # 넥슨 고유 게임
        'tags': ['sports', 'soccer', 'simulation', 'multiplayer', 'competitive', 'free-to-play', 'korean'],
    },
    
    # === 디아블로 / 핵앤슬래시 ===
    {
        'title': '디아블로 II: 레저렉션 (Diablo II: Resurrected)',
        'genre': 'Action RPG, Hack and Slash, Dungeon Crawler',
        'description': '블리자드의 핵앤슬래시 RPG 리마스터. 한국 온라인게임 문화에 큰 영향. 아이템 파밍, 공포, 우울한 분위기.',
        'image_url': '/img/diablo2.jpg',
        'steam_appid': None,
        'skip_rawg': True,
        'tags': ['action-rpg', 'hack-and-slash', 'dungeon-crawler', 'dark-fantasy', 'loot'],
    },
    {
        'title': '디아블로 III (Diablo III)',
        'genre': 'Action RPG, Hack and Slash',
        'description': '디아블로 시리즈 3편. 시즌제 운영과 그레이터 리프트 시스템.',
        'image_url': '/img/diablo3.jpg',  # 수동 이미지 필요 (Battle.net 전용)
        'steam_appid': None,  # Battle.net 전용
        'skip_rawg': True,  # 수동 이미지 사용
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
        'image_url': '/img/Genshin_Impact.jpg',
        'steam_appid': None,  # Epic/자체 런처
        'tags': ['action-rpg', 'open-world', 'gacha', 'anime', 'exploration', 'free-to-play'],
    },
    {
        'title': '블루아카이브 (Blue Archive)',
        'genre': 'RPG, Strategy, Gacha, Anime',
        'description': '넥슨게임즈의 미소녀 수집형 RPG. 학원물 세계관과 일러스트가 인기.',
        'image_url': '/img/blue_archive.jpg',  # 수동 이미지 (RAWG에서 잘못된 이미지 제공)
        'skip_rawg': True,  # 모바일 게임
        'tags': ['rpg', 'strategy', 'gacha', 'anime', 'visual-novel', 'free-to-play', 'korean'],
    },
    
    # === 기타 클래식 ===
    {
        'title': '바람의나라 (Kingdom of the Winds)',
        'genre': 'MMORPG, 2D, Korean Mythology',
        'description': '넥슨의 원조 그래픽 MMORPG. 1996년 서비스 시작. 고구려 신화 기반.',
        'image_url': '/img/wind.jpg',
        'skip_rawg': True,
        'tags': ['mmorpg', '2d', 'korean', 'mythology', 'classic', 'free-to-play'],
    },
    {
        'title': '뮤 (MU Online)',
        'genre': 'MMORPG, 3D, Fantasy',
        'description': '웹젠의 3D MMORPG. 초기 3D 온라인게임 대표. 아이템 +13 강화 시스템의 원조.',
        'image_url': '/img/mu.jpg',
        'skip_rawg': True,
        'tags': ['mmorpg', '3d', 'fantasy', 'pvp', 'free-to-play', 'korean'],
    },
    {
        'title': '거상 (Gersang)',
        'genre': 'MMORPG, Trading, Economy',
        'description': '넥슨 초기 게임. 조선시대 배경의 무역과 경제 시스템이 특징인 온라인 게임.',
        'image_url': '/img/Gersang.jpg',
        'skip_rawg': True,
        'tags': ['mmorpg', 'economy', 'trading', 'korean', 'classic', 'free-to-play'],
    },
    {
        'title': '그랜드체이스 (GrandChase)',
        'genre': 'Action RPG, Beat em up, 2D',
        'description': 'KOG에서 개발한 횡스크롤 액션 RPG. 던파와 유사한 벨트스크롤 액션. 엘소드의 전신.',
        'image_url': '/img/GrandChase.jpg',
        'skip_rawg': True,
        'tags': ['action-rpg', 'beat-em-up', '2d', 'anime', 'free-to-play', 'korean'],
    },
    {
        'title': '엘소드 (Elsword)',
        'genre': 'Action RPG, Beat em up, 2D, Anime',
        'description': 'KOG의 횡스크롤 액션 RPG. 그랜드체이스의 후속작. 화려한 스킬과 콤보.',
        'image_url': '/img/elsword.jpg',
        'skip_rawg': True,
        'tags': ['action-rpg', 'beat-em-up', '2d', 'anime', 'free-to-play', 'korean'],
    },
    {
        'title': '메이플스토리 2 (MapleStory 2)',
        'genre': 'MMORPG, 3D, Casual, Building',
        'description': '메이플스토리의 3D 버전. 집꾸미기와 UGC 컨텐츠가 특징. 서비스 종료.',
        'image_url': '/img/MapleStory2.jpg',
        'skip_rawg': True,
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
        'image_url': '/img/Brawl_Stars.jpg',
        'skip_rawg': True,
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
        'image_url': '/img/ClashRoyale.jpg',
        'skip_rawg': True,
        'tags': ['strategy', 'card-game', 'tower-defense', 'pvp', 'competitive', 'free-to-play'],
    },
    {
        'title': '어몽어스 (Among Us)',
        'genre': 'Social Deduction, Party Game, Multiplayer',
        'description': '마피아 게임을 온라인으로. 크루원과 임포스터로 나뉘어 정체를 찾아내는 게임.',
        'image_url': 'https://cdn.akamai.steamstatic.com/steam/apps/945360/header.jpg',
        'steam_appid': 945360,
        'skip_rawg': True,  # RAWG에서 Among Us 3D, VR, Wolf Among Us 등 혼동됨
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
        'image_url': '/img/Roblox.jpg',
        'skip_rawg': True,
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
        'image_url': '/img/cookierun.jpg',
        'skip_rawg': True,
        'tags': ['rpg', 'simulation', 'gacha', 'cute', 'building', 'free-to-play', 'korean'],
    },
    {
        'title': '니케 (NIKKE: Goddess of Victory)',
        'genre': 'Shooter, RPG, Gacha, Anime',
        'description': '시프트업의 미소녀 슈팅 가챠게임. 화려한 일러스트와 슈팅 액션.',
        'image_url': '/img/nikke.jpg',
        'skip_rawg': True,
        'tags': ['shooter', 'rpg', 'gacha', 'anime', 'action', 'free-to-play', 'korean'],
    },
    {
        'title': '명일방주 (Arknights)',
        'genre': 'Tower Defense, Strategy, Gacha',
        'description': '하이퍼그리프의 타워 디펜스 가챠게임. 전략적인 배치와 캐릭터 수집.',
        'image_url': '/img/Arknights.jpg',
        'skip_rawg': True,
        'tags': ['tower-defense', 'strategy', 'gacha', 'anime', 'tactical', 'free-to-play'],
    },
    {
        'title': '붕괴: 스타레일 (Honkai: Star Rail)',
        'genre': 'Turn-based RPG, Gacha, Sci-Fi',
        'description': '호요버스의 턴제 RPG. 우주를 배경으로 한 스토리와 캐릭터 수집.',
        'image_url': '/img/Star_Rail.jpg',
        'skip_rawg': True,
        'tags': ['turn-based', 'rpg', 'gacha', 'anime', 'sci-fi', 'story-rich', 'free-to-play'],
    },
    {
        'title': '명조: 워더링 웨이브 (Wuthering Waves)',
        'genre': 'Action RPG, Open World, Gacha',
        'description': '쿠로게임즈의 오픈월드 액션 RPG. 원신과 경쟁하는 신작.',
        'image_url': '/img/Waves.jpg',
        'skip_rawg': True,
        'tags': ['action-rpg', 'open-world', 'gacha', 'anime', 'exploration', 'free-to-play'],
    },
    {
        'title': '우마무스메 (Umamusume: Pretty Derby)',
        'genre': 'Simulation, Racing, Gacha, Anime',
        'description': '말을 의인화한 레이싱 육성 시뮬레이션. 일본에서 큰 인기.',
        'image_url': '/img/mal.jpg',
        'tags': ['simulation', 'racing', 'gacha', 'anime', 'cute', 'free-to-play'],
    },
    {
        'title': '페그오 (Fate/Grand Order)',
        'genre': 'Turn-based RPG, Gacha, Visual Novel',
        'description': '페이트 시리즈의 모바일 RPG. 역사 영웅들을 소환하는 가챠 게임.',
        'image_url': '/img/fgo.jpg',
        'skip_rawg': True,
        'tags': ['turn-based', 'rpg', 'gacha', 'anime', 'visual-novel', 'story-rich', 'free-to-play'],
    },
    {
        'title': '리그 오브 레전드: 와일드 리프트 (LoL: Wild Rift)',
        'genre': 'MOBA, Strategy, Multiplayer',
        'description': '롤의 모바일 버전. 모바일에 최적화된 조작과 빠른 게임 시간.',
        'image_url': '/img/Wild_Rift.jpg',
        'skip_rawg': True,
        'tags': ['moba', 'strategy', 'team-based', 'competitive', 'esports', 'free-to-play'],
    },
    {
        'title': '팀파이트 택틱스 (Teamfight Tactics)',
        'genre': 'Auto Battler, Strategy, Multiplayer',
        'description': '롤 세계관의 오토배틀러. 챔피언 조합과 시너지가 핵심.',
        'image_url': '/img/Teamfight_Tactics.jpg',
        'skip_rawg': True,
        'tags': ['auto-battler', 'strategy', 'pvp', 'tactical', 'free-to-play'],
    },
    
    # === 닌텐도 1세대 클래식 ===
    {
        'title': '슈퍼 마리오 시리즈 (Super Mario Bros.)',
        'genre': 'Platformer, Action, Adventure',
        'description': '닌텐도의 대표 프랜차이즈. 배관공 마리오의 모험을 그린 플랫포머의 교과서.',
        'image_url': '/img/Super_Mario_Bros.jpg',
        'skip_rawg': True,
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
        'image_url': '/img/Mario_Kart.jpg',
        'skip_rawg': True,
        'tags': ['racing', 'arcade', 'multiplayer', 'party-game', 'family-friendly', 'nintendo'],
    },
    {
        'title': '마리오 파티 슈퍼스타즈 (Mario Party Superstars)',
        'genre': 'Party Game, Minigames, Multiplayer',
        'description': '닌텐도 파티게임 시리즈. 보드게임과 미니게임의 조합.',
        'image_url': '/img/Mario_Party.jpg',
        'skip_rawg': True,
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
        'image_url': '/img/Links_Awakening.jpg',
        'tags': ['action-adventure', 'puzzle', 'cute', 'nintendo', 'classic'],
    },
    
    # === 포켓몬 시리즈 ===
    {
        'title': '포켓몬스터 스칼렛/바이올렛 (Pokémon Scarlet/Violet)',
        'genre': 'RPG, Monster Collection, Open World',
        'description': '최초의 오픈월드 포켓몬. 스페인 풍 지역을 탐험하며 포켓몬 수집.',
        'image_url': '/img/Pokemon_Sv.jpg',
        'skip_rawg': True,
        'tags': ['rpg', 'monster-tamer', 'open-world', 'turn-based', 'nintendo', 'adventure'],
    },
    {
        'title': '포켓몬스터 소드/실드 (Pokémon Sword/Shield)',
        'genre': 'RPG, Monster Collection, Adventure',
        'description': '스위치 첫 본편 포켓몬. 와일드 에리어와 다이맥스 배틀.',
        'image_url': '/img/Pokemon_Ss.jpg',
        'tags': ['rpg', 'monster-tamer', 'adventure', 'turn-based', 'nintendo'],
    },
    {
        'title': '포켓몬 레전드 아르세우스 (Pokémon Legends: Arceus)',
        'genre': 'Action RPG, Monster Collection, Open World',
        'description': '과거 시대 포켓몬 세계. 액션 기반 야생 포켓몬 포획.',
        'image_url': '/img/LEGENDS_Arceus.jpg',
        'skip_rawg': True,
        'tags': ['action-rpg', 'monster-tamer', 'open-world', 'exploration', 'nintendo'],
    },
    {
        'title': '포켓몬스터 다이아몬드/펄',
        'genre': 'RPG, Monster Collection',
        'description': '4세대 포켓몬의 스위치 리메이크. 신오지방 모험.',
        'image_url': '/img/Pokemon_dp.jpg',
        'tags': ['rpg', 'monster-tamer', 'adventure', 'turn-based', 'nintendo', 'classic'],
    },
    {
        'title': '포켓몬스터 레츠고 피카츄/이브이 (Pokémon Let\'s Go)',
        'genre': 'RPG, Monster Collection, Casual',
        'description': '포켓몬 GO 스타일의 본편 게임. 모션 컨트롤 포획.',
        'image_url': '/img/Pokemon_lets.jpg',
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
        'image_url': '/img/Ac_Wild_World.jpg',
        'skip_rawg': True,
        'tags': ['life-sim', 'relaxing', 'casual', 'cute', 'nintendo', 'classic'],
    },
    
    # === 스플래툰 시리즈 ===
    {
        'title': '스플래툰 3 (Splatoon 3)',
        'genre': 'TPS, Shooter, Multiplayer',
        'description': '잉크를 뿌려 영역을 확보하는 슈터. 유니크한 게임성과 스타일리시한 디자인.',
        'image_url': '/img/Splatoon_.jpg',
        'skip_rawg': True,
        'tags': ['shooter', 'tps', 'multiplayer', 'team-based', 'competitive', 'nintendo', 'colorful'],
    },
    
    # === 커비 시리즈 ===
    {
        'title': '별의 커비: 디스커버리 (Kirby and the Forgotten Land)',
        'genre': 'Platformer, Action, Adventure',
        'description': '커비 시리즈 첫 3D 플랫포머. 머금기와 입체운동 능력.',
        'image_url': '/img/Kirby_and_the_Forgotten_Land.jpg',
        'skip_rawg': True,
        'tags': ['platformer', 'action', 'adventure', 'cute', 'nintendo', 'family-friendly'],
    },
    {
        'title': '별의 커비 스타 얼라이즈 (Kirby Star Allies)',
        'genre': 'Platformer, Action, Co-op',
        'description': '스위치용 커비. 적을 동료로 만드는 시스템.',
        'image_url': '/img/Kirby_Star_Allies.jpg',
        'skip_rawg': True,
        'tags': ['platformer', 'action', 'co-op', 'cute', 'nintendo', 'family-friendly'],
    },
    
    # === 피트니스/리듬/파티 게임 ===
    {
        'title': '링피트 어드벤처 (Ring Fit Adventure)',
        'genre': 'Fitness, RPG, Adventure',
        'description': '링콘 컨트롤러로 운동하며 모험하는 피트니스 게임.',
        'image_url': '/img/Ring_Fit_Adventure.jpg',
        'skip_rawg': True,
        'tags': ['fitness', 'rpg', 'adventure', 'casual', 'nintendo', 'family-friendly'],
    },
    {
        'title': '저스트 댄스 2024 (Just Dance 2024)',
        'genre': 'Rhythm, Dance, Music',
        'description': '유비소프트의 댄스 게임. K-POP 포함 다양한 곡 수록.',
        'image_url': '/img/Just_Dance.jpg',
        'skip_rawg': True,
        'tags': ['rhythm', 'music', 'fitness', 'party-game', 'casual', 'family-friendly'],
    },
    {
        'title': '리듬 세상 (Rhythm Heaven)',
        'genre': 'Rhythm, Music, Minigames',
        'description': '닌텐도의 리듬 게임. 기발한 미니게임과 중독성 있는 음악.',
        'image_url': '/img/Rhythm_Heaven.jpg',
        'skip_rawg': True,
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
        'image_url': '/img/Professor_Layton.jpg',
        'skip_rawg': True,
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
        'image_url': '/img/Fire_Emblem_Three_Houses.jpg',
        'skip_rawg': True,
        'tags': ['tactical-rpg', 'strategy', 'story-rich', 'anime', 'turn-based', 'nintendo'],
    },
    {
        'title': '파이어 엠블렘 인게이지 (Fire Emblem Engage)',
        'genre': 'Tactical RPG, Strategy',
        'description': '역대 FE 영웅들이 등장하는 신작. 전략적 깊이와 팬서비스.',
        'image_url': '/img/Fire_Emblem_Engage.jpg',
        'skip_rawg': True,
        'tags': ['tactical-rpg', 'strategy', 'anime', 'turn-based', 'nintendo'],
    },
    {
        'title': '제노블레이드 크로니클스 3 (Xenoblade Chronicles 3)',
        'genre': 'JRPG, Action RPG, Open World',
        'description': '모노리스 소프트의 대작 JRPG. 방대한 월드와 스토리.',
        'image_url': '/img/Xenoblade_Chronicles3.jpg',
        'skip_rawg': True,
        'tags': ['jrpg', 'action-rpg', 'open-world', 'story-rich', 'nintendo'],
    },
    {
        'title': '메트로이드 드레드 (Metroid Dread)',
        'genre': 'Metroidvania, Action, Exploration',
        'description': '19년 만의 메트로이드 2D 신작. 긴장감 넘치는 탐험.',
        'image_url': '/img/Metroid.jpg',
        'skip_rawg': True,
        'tags': ['metroidvania', 'action', 'exploration', 'sci-fi', 'nintendo'],
    },
    {
        'title': '동키콩 바난자',
        'genre': 'Platformer, Action, Co-op',
        'description': '레트로 스튜디오의 동키콩 부활작. 하드코어 플랫포머.',
        'image_url': '/img/DONKEY_KONG_BANANZA.jpg',
        'skip_rawg': True,
        'tags': ['platformer', 'action', 'co-op', 'difficult', 'nintendo', 'classic'],
    },
    {
        'title': '요시 시리즈 (Yoshi\'s Crafted World)',
        'genre': 'Platformer, Puzzle, Cute',
        'description': '공예 스타일의 요시 게임. 귀엽고 창의적인 스테이지.',
        'image_url': '/img/Yoshi\'s_Crafted_World.jpg',
        'skip_rawg': True,
        'tags': ['platformer', 'puzzle', 'cute', 'casual', 'nintendo', 'family-friendly'],
    },
    {
        'title': '피크민 4 (Pikmin 4)',
        'genre': 'Strategy, Puzzle, Adventure',
        'description': '미야모토의 피크민 시리즈. 작은 생물들을 지휘해 탐험.',
        'image_url': '/img/Pikmin4.jpg',
        'skip_rawg': True,
        'tags': ['strategy', 'puzzle', 'adventure', 'cute', 'nintendo'],
    },
    {
        'title': '루이지 맨션 3 (Luigi\'s Mansion 3)',
        'genre': 'Action-Adventure, Puzzle, Horror',
        'description': '루이지의 유령 저택 탐험. 코믹 호러 어드벤처.',
        'image_url': '/img/Luigi_Mansion_3.jpg',
        'skip_rawg': True,
        'tags': ['action-adventure', 'puzzle', 'horror', 'funny', 'nintendo', 'co-op'],
    },

    {
        'title': '테트리스 99 (Tetris 99)',
        'genre': 'Puzzle, Battle Royale, Multiplayer',
        'description': '테트리스 배틀로얄. 99명 중 최후의 1인.',
        'image_url': '/img/Tetris99.jpg',
        'skip_rawg': True,
        'tags': ['puzzle', 'battle-royale', 'multiplayer', 'competitive', 'nintendo', 'free-to-play'],
    },
    
    # === 전세계 인기 무료 게임 (F2P) ===
    {
        'title': '팀 포트리스 2 (Team Fortress 2)',
        'genre': 'FPS, Hero Shooter, Multiplayer',
        'description': '밸브의 클래스 기반 팀 슈터. 9개의 개성 있는 클래스와 유머러스한 스타일. 2007년 출시 후 무료화되어 꾸준한 인기.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/5/5e/Team_Fortress_2_cover.jpg',
        'steam_appid': 440,
        'tags': ['fps', 'hero-shooter', 'multiplayer', 'team-based', 'funny', 'free-to-play', 'classic'],
    },
    {
        'title': '도타 2 (Dota 2)',
        'genre': 'MOBA, Strategy, Multiplayer',
        'description': '밸브의 MOBA 대작. 워크래프트 3 Dota Allstars를 계승. e스포츠 역대 최고 상금 기록. 깊은 전략성과 팀플레이.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/0/05/Dota_2_Logo.png',
        'steam_appid': 570,
        'tags': ['moba', 'strategy', 'multiplayer', 'competitive', 'esports', 'free-to-play', 'team-based'],
    },
    {
        'title': '에이펙스 레전드 (Apex Legends)',
        'genre': 'Battle Royale, FPS, Hero Shooter',
        'description': '리스폰 엔터테인먼트의 배틀로얄 FPS. 레전드별 고유 능력과 빠른 무브먼트가 특징. 타이탄폴 세계관.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/d/db/Apex_legends_cover.jpg',
        'steam_appid': 1172470,
        'tags': ['battle-royale', 'fps', 'hero-shooter', 'multiplayer', 'competitive', 'free-to-play', 'team-based'],
    },
    {
        'title': '포트나이트 (Fortnite)',
        'genre': 'Battle Royale, TPS, Building',
        'description': '에픽게임즈의 배틀로얄 게임. 건축 시스템이 특징. 콘서트, 콜라보 등 문화 현상으로 성장.',
        'image_url': '/img/Fortnite.jpg',
        'skip_rawg': True,
        'tags': ['battle-royale', 'tps', 'building', 'multiplayer', 'competitive', 'free-to-play', 'creative'],
    },
    {
        'title': '워프레임 (Warframe)',
        'genre': 'Action, TPS, Co-op, Looter',
        'description': '디지털 익스트림즈의 무료 액션 TPS. 닌자 스타일의 빠른 액션과 다양한 프레임(캐릭터) 수집.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/e/e9/Warframe_Cover_Art.png',
        'steam_appid': 230410,
        'tags': ['action', 'tps', 'co-op', 'loot', 'sci-fi', 'free-to-play', 'ninja'],
    },
    {
        'title': 'Path of Exile',
        'genre': 'Action RPG, Hack and Slash, Dungeon Crawler',
        'description': '그라인딩 기어 게임즈의 핵앤슬래시 ARPG. 디아블로 정신적 후속작. 복잡한 스킬 시스템과 시즌제 운영.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/9/91/Path_of_Exile_cover.png',
        'steam_appid': 238960,
        'tags': ['action-rpg', 'hack-and-slash', 'dungeon-crawler', 'loot', 'dark-fantasy', 'free-to-play'],
    },
    {
        'title': 'Path of Exile 2',
        'genre': 'Action RPG, Hack and Slash, Dungeon Crawler',
        'description': 'Path of Exile의 후속작. 새로운 캐릭터와 스토리, 개선된 그래픽과 게임플레이.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/9/91/Path_of_Exile_cover.png',
        'steam_appid': 2694490,
        'tags': ['action-rpg', 'hack-and-slash', 'dungeon-crawler', 'loot', 'dark-fantasy', 'free-to-play'],
    },
    {
        'title': '데스티니 가디언즈 (Destiny 2)',
        'genre': 'FPS, Looter Shooter, MMO',
        'description': '번지의 온라인 FPS. SF 세계관에서 가디언이 되어 싸우는 루트 슈터. 레이드 컨텐츠로 유명.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/0/05/Destiny_2_%28artwork%29.jpg',
        'steam_appid': 1085660,
        'tags': ['fps', 'shooter', 'loot', 'mmo', 'sci-fi', 'co-op', 'free-to-play'],
    },
    {
        'title': '월드 오브 탱크 (World of Tanks)',
        'genre': 'Action, Simulation, Multiplayer',
        'description': '워게이밍의 전차 전투 게임. 2차대전~냉전기 전차로 15vs15 팀 배틀.',
        'image_url': '/img/World_Of_Tanks.jpg',
        'tags': ['action', 'simulation', 'multiplayer', 'military', 'tank', 'free-to-play', 'team-based'],
    },
    {
        'title': '워 썬더 (War Thunder)',
        'genre': 'Simulation, Combat, Multiplayer',
        'description': '가이진 엔터테인먼트의 밀리터리 시뮬레이션. 전차, 항공기, 함선을 모두 조종 가능.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/b/b8/War_Thunder_logo.png',
        'steam_appid': 236390,
        'tags': ['simulation', 'combat', 'multiplayer', 'military', 'vehicle', 'free-to-play'],
    },
    {
        'title': '원스 휴먼 (Once Human)',
        'genre': 'Survival, Open World, TPS, Co-op',
        'description': '스타리 스튜디오의 오픈월드 서바이벌 게임. 포스트 아포칼립스 세계에서 기이한 생물들과 싸우며 생존.',
        'image_url': 'https://cdn.akamai.steamstatic.com/steam/apps/2139460/header.jpg',
        'steam_appid': 2139460,
        'tags': ['survival', 'open-world', 'tps', 'co-op', 'post-apocalyptic', 'free-to-play', 'building'],
    },
    {
        'title': '연운 (Where Winds Meet)',
        'genre': 'Action RPG, Martial Arts, Open World',
        'description': '에버스톤 스튜디오의 중국풍 무협 오픈월드 액션 RPG. 화려한 경공술과 전투 액션이 특징.',
        'image_url': '/img/wherewindsmeet.jpg',
        'steam_appid': 1399560,
        'skip_rawg': True,  # 중국 게임이라 RAWG 매칭 불확실
        'tags': ['action-rpg', 'martial-arts', 'open-world', 'exploration', 'free-to-play', 'anime'],
    },
    {
        'title': 'Counter-Strike 2',
        'genre': 'FPS, Tactical Shooter, Competitive',
        'description': 'CS:GO의 후속작. 소스2 엔진으로 리메이크된 밸브의 대표 FPS. e스포츠의 성지.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/e/e5/Counter-Strike_2_-_Cover_Art.jpg',
        'steam_appid': 730,
        'tags': ['fps', 'tactical-shooter', 'competitive', 'esports', 'multiplayer', 'free-to-play'],
    },
    {
        'title': 'SMITE 2',
        'genre': 'MOBA, Action, Mythology',
        'description': '하이레즈 스튜디오의 3인칭 MOBA. 신화 속 신들로 플레이.',
        'image_url': '/img/smite2.jpg',  # 수동 이미지 필요
        'steam_appid': 2437690,
        'skip_rawg': True,  # 정확한 이미지 확보 위해
        'tags': ['moba', 'action', 'mythology', 'multiplayer', 'competitive', 'free-to-play', 'tps'],
    },
    {
        'title': '이터널 리턴 (Eternal Return)',
        'genre': 'Battle Royale, MOBA, Survival',
        'description': '님블뉴론의 배틀로얄 + MOBA 하이브리드. 한국 개발 게임으로 아이템 제작과 생존.',
        'image_url': 'https://cdn.akamai.steamstatic.com/steam/apps/1049590/header.jpg',
        'steam_appid': 1049590,
        'tags': ['battle-royale', 'moba', 'survival', 'anime', 'competitive', 'free-to-play', 'korean'],
    },
    {
        'title': '나라카: 블레이드포인트 (NARAKA: BLADEPOINT)',
        'genre': 'Battle Royale, Action, Martial Arts',
        'description': '24 엔터테인먼트의 무협 배틀로얄. 근접 무기 중심 전투와 경공술.',
        'image_url': 'https://upload.wikimedia.org/wikipedia/en/2/24/Naraka_Bladepoint.jpg',
        'steam_appid': 1203220,
        'tags': ['battle-royale', 'action', 'martial-arts', 'multiplayer', 'competitive', 'free-to-play'],
    },
    {
        'title': '더 파이널스 (THE FINALS)',
        'genre': 'FPS, Arena Shooter, Destruction',
        'description': '엠바크 스튜디오의 파괴 가능한 환경의 FPS. 실시간 방송 컨셉의 게임쇼.',
        'image_url': 'https://cdn.akamai.steamstatic.com/steam/apps/2073850/header.jpg',
        'steam_appid': 2073850,
        'tags': ['fps', 'shooter', 'destruction', 'multiplayer', 'competitive', 'free-to-play', 'team-based'],
    },
    {
        'title': '마블 라이벌 (Marvel Rivals)',
        'genre': 'Hero Shooter, TPS, Team-based',
        'description': '넷이즈의 마블 히어로 슈터. 오버워치 스타일의 6v6 팀 배틀.',
        'image_url': 'https://cdn.akamai.steamstatic.com/steam/apps/2767030/header.jpg',
        'steam_appid': 2767030,
        'tags': ['hero-shooter', 'tps', 'team-based', 'competitive', 'multiplayer', 'free-to-play'],
    },
    # 벨루시아, 스쿼드44 제거 - 한국에서 유행하지 않음
    {
        'title': '카트라이더 드리프트 (KartRider Drift)',
        'genre': 'Racing, Arcade, Multiplayer',
        'description': '넥슨의 카트라이더 글로벌 버전. 크로스플랫폼 지원. 기존 카트라이더와는 별개 게임.',
        'image_url': '/img/kartrider_drift.jpg',  # 수동 이미지 필요
        'steam_appid': 2073450,
        'skip_rawg': True,  # 기존 카트라이더와 구분
        'tags': ['racing', 'arcade', 'multiplayer', 'casual', 'free-to-play', 'korean', '3d'],
    },
    {
        'title': '메이플스토리 월드 (MapleStory Worlds)',
        'genre': 'MMORPG, Sandbox, Creative',
        'description': '메이플스토리의 유저 제작 콘텐츠 플랫폼. 로블록스 스타일의 창작 도구.',
        'image_url': '/img/maplestorywolrd.jpg',
        'steam_appid': 1913930,
        'skip_rawg': True,  # 한국 게임
        'tags': ['mmorpg', 'sandbox', 'creative', 'casual', 'free-to-play', 'korean', '2d'],
    },
]



class Command(BaseCommand):
    help = '한국에서 유행했던 유명 온라인/PC방 게임들을 DB에 추가합니다 (RAWG API 연동)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='기존 한국 게임 데이터 삭제 후 재생성',
        )
        parser.add_argument(
            '--fetch-rawg',
            action='store_true',
            help='RAWG API에서 추가 정보 가져오기 (이미지, 설명 등)',
        )
        parser.add_argument(
            '--update-images',
            action='store_true',
            help='기존 게임의 이미지만 RAWG에서 업데이트',
        )
    
    def handle(self, *args, **options):
        import time
        import requests
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        RAWG_API_KEY = os.getenv('RAWG_API_KEY', '')
        
        self.stdout.write("한국 유명 게임 데이터 추가 시작...")
        
        # 태그 생성 먼저
        self._ensure_tags()
        
        created_count = 0
        updated_count = 0
        rawg_fetched = 0
        
        for idx, game_data in enumerate(KOREAN_POPULAR_GAMES):
            title = game_data['title']
            
            # 기존 게임 찾기 (제목 또는 steam_appid로)
            # 한글 부분만 또는 영문 부분만으로도 검색
            title_parts = title.split(' (')
            korean_title = title_parts[0].strip()
            english_title = title_parts[1].rstrip(')').strip() if len(title_parts) > 1 else None
            
            existing = Game.objects.filter(title__icontains=korean_title).first()
            if not existing and english_title:
                existing = Game.objects.filter(title__icontains=english_title).first()
            
            # steam_appid로도 검색 (제목 변경 시 기존 게임을 찾기 위해)
            if not existing and game_data.get('steam_appid'):
                existing = Game.objects.filter(steam_appid=game_data['steam_appid']).first()
            
            # skip_rawg 플래그 확인 - RAWG에 없거나 잘못 매칭되는 게임은 건너뜀
            skip_rawg = game_data.get('skip_rawg', False)
            
            # Steam CDN 이미지 URL 생성 (steam_appid가 있는 경우)
            steam_cdn_image = None
            if game_data.get('steam_appid'):
                steam_cdn_image = f"https://cdn.akamai.steamstatic.com/steam/apps/{game_data['steam_appid']}/header.jpg"
            
            # RAWG에서 데이터 가져오기 (skip_rawg가 아닌 경우에만)
            rawg_data = None
            if not skip_rawg and (options.get('fetch_rawg') or options.get('update_images')) and RAWG_API_KEY:
                search_term = english_title or korean_title
                rawg_data = self._fetch_from_rawg(search_term, RAWG_API_KEY)
                if rawg_data:
                    # RAWG 매칭 결과 유사도 검증 (개선된 버전)
                    rawg_name = rawg_data.get('name') or ''
                    is_match = self._is_similar_title(search_term, rawg_name)
                    
                    if is_match:
                        rawg_fetched += 1
                        self.stdout.write(f"  🔍 RAWG 매칭: {title} → {rawg_data.get('name')}")
                    else:
                        self.stdout.write(self.style.WARNING(f"  ⚠️ RAWG 불일치: {title} → {rawg_data.get('name')} (무시)"))
                        rawg_data = None  # 불일치하면 무시
                time.sleep(0.3)  # API 레이트 리밋 방지
            elif skip_rawg:
                self.stdout.write(f"  ⏭️ RAWG 건너뜀: {title} (skip_rawg=True)")
            
            if existing:
                if options['delete']:
                    existing.delete()
                    self.stdout.write(f"  삭제: {title}")
                else:
                    # 업데이트
                    if not existing.description:
                        existing.description = game_data.get('description', existing.description)
                    existing.genre = game_data.get('genre', existing.genre)
                    
                    # 이미지 업데이트 우선순위:
                    # 1) game_data에 수동 지정된 image_url (가장 높은 우선순위)
                    # 2) Steam CDN 이미지 (steam_appid가 있는 경우)
                    # 3) RAWG 데이터 (skip_rawg가 아닌 경우)
                    manual_image = game_data.get('image_url', '')
                    
                    # 수동 지정 이미지가 있으면 무조건 적용
                    if manual_image:
                        existing.image_url = manual_image
                        if not existing.background_image:
                            existing.background_image = manual_image
                        self.stdout.write(f"    📷 이미지 수동 지정: {manual_image[:50]}...")
                    # Steam CDN 이미지 (수동 지정이 없고 steam_appid가 있는 경우)
                    elif steam_cdn_image and not existing.image_url:
                        existing.image_url = steam_cdn_image
                        existing.background_image = steam_cdn_image
                        self.stdout.write(f"    📷 Steam CDN 이미지: {steam_cdn_image[:50]}...")
                    
                    # RAWG 데이터로 업데이트 (이미지는 수동/Steam이 없을 때만)
                    if rawg_data:
                        if not existing.rawg_id:
                            existing.rawg_id = rawg_data.get('id')
                        # 이미지: 수동 지정이나 Steam CDN이 없을 때만 RAWG 사용
                        if not manual_image and not steam_cdn_image:
                            if not existing.background_image or options.get('update_images'):
                                existing.background_image = rawg_data.get('background_image', '')
                                existing.image_url = rawg_data.get('background_image', existing.image_url)
                        if rawg_data.get('metacritic') and not existing.metacritic_score:
                            existing.metacritic_score = rawg_data.get('metacritic')
                        if rawg_data.get('description_raw') and not existing.description:
                            existing.description = rawg_data.get('description_raw')[:2000]
                    
                    existing.save()
                    
                    # 기존 게임에도 태그 연결 (누락된 태그만 추가)
                    tag_slugs = game_data.get('tags', [])
                    for slug in tag_slugs:
                        tag = Tag.objects.filter(slug=slug).first()
                        if tag and not existing.tags.filter(pk=tag.pk).exists():
                            existing.tags.add(tag)
                    
                    updated_count += 1
                    self.stdout.write(f"  업데이트: {title}")
                    continue
            
            # 새 게임 생성
            image_url = game_data.get('image_url', '')
            background_image = ''
            rawg_id = None
            metacritic = None
            description = game_data.get('description', '')
            
            # 이미지 우선순위: 1) Steam CDN, 2) 수동 지정, 3) RAWG
            if steam_cdn_image:
                # Steam AppID가 있으면 Steam CDN 이미지 우선
                background_image = steam_cdn_image
                if not image_url:
                    image_url = steam_cdn_image
            
            # RAWG 데이터 사용 (skip_rawg가 아닌 경우에만)
            if rawg_data:
                rawg_id = rawg_data.get('id')
                # RAWG 이미지는 수동 지정이 없을 때만 사용
                if rawg_data.get('background_image') and not game_data.get('image_url'):
                    image_url = rawg_data.get('background_image')
                    background_image = rawg_data.get('background_image')
                metacritic = rawg_data.get('metacritic')
                if rawg_data.get('description_raw') and not description:
                    description = rawg_data.get('description_raw')[:2000]
            
            game = Game.objects.create(
                title=title,
                genre=game_data.get('genre', ''),
                description=description,
                image_url=image_url,
                background_image=background_image,
                steam_appid=game_data.get('steam_appid'),
                rawg_id=rawg_id,
                metacritic_score=metacritic,
            )
            
            # 태그 연결
            tag_slugs = game_data.get('tags', [])
            for slug in tag_slugs:
                tag = Tag.objects.filter(slug=slug).first()
                if tag:
                    game.tags.add(tag)
            
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"  추가: {title}"))
        
        # 온보딩 캐시 무효화 (변경사항 즉시 반영)
        try:
            from users.onboarding import clear_korean_games_cache
            clear_korean_games_cache()
            self.stdout.write(self.style.SUCCESS("📝 온보딩 캐시 무효화 완료"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ 캐시 무효화 실패: {e}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"\n완료! 생성: {created_count}개, 업데이트: {updated_count}개, RAWG 매칭: {rawg_fetched}개"
        ))
    
    def _fetch_from_rawg(self, search_term, api_key):
        """RAWG API에서 게임 검색하여 상세 정보 반환"""
        import requests
        
        try:
            # 1. 검색
            search_url = f"https://api.rawg.io/api/games"
            params = {
                'key': api_key,
                'search': search_term,
                'page_size': 1,
            }
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code != 200:
                return None
            
            data = response.json()
            results = data.get('results', [])
            if not results:
                return None
            
            game_id = results[0].get('id')
            
            # 2. 상세 정보 가져오기
            detail_url = f"https://api.rawg.io/api/games/{game_id}"
            detail_response = requests.get(detail_url, params={'key': api_key}, timeout=10)
            if detail_response.status_code == 200:
                return detail_response.json()
            
            return results[0]  # 상세 정보 실패 시 검색 결과 반환
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  RAWG 오류: {e}"))
            return None
    
    def _is_similar_title(self, search_term, rawg_name):
        """
        두 게임 제목이 유사한지 확인 (개선된 매칭 로직)
        
        매칭 케이스:
        - "Dungeon & Fighter" vs "Dungeon Fighter Online" → True
        - "Lineage II" vs "Lineage 2: The Chaotic Chronicle" → True
        - "PUBG: BATTLEGROUNDS" vs "PlayerUnknown's Battlegrounds" → True
        - "NIKKE: Goddess of Victory" vs "GODDESS OF VICTORY: NIKKE" → True
        - "Blade & Soul" vs "Soul Edge" → False (다른 게임)
        """
        import re
        
        def normalize(text):
            """제목 정규화: 소문자, 특수문자 제거, 단어 추출"""
            text = text.lower()
            # 로마 숫자 → 아라비아 숫자
            text = text.replace(' ii', ' 2').replace(' iii', ' 3').replace(' iv', ' 4')
            # 특수문자 제거 (알파벳, 숫자, 공백만 유지)
            text = re.sub(r'[^a-z0-9\s]', ' ', text)
            # 여러 공백을 하나로
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        def get_key_words(text):
            """핵심 단어만 추출 (불용어 제거)"""
            stopwords = {'the', 'a', 'an', 'of', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
            words = normalize(text).split()
            return set(w for w in words if w not in stopwords and len(w) > 1)
        
        # 정규화된 문자열
        norm_search = normalize(search_term)
        norm_rawg = normalize(rawg_name)
        
        # 1. 정규화된 문자열이 서로 포함되면 매칭
        if norm_search in norm_rawg or norm_rawg in norm_search:
            return True
        
        # 2. 핵심 단어 기반 매칭
        search_words = get_key_words(search_term)
        rawg_words = get_key_words(rawg_name)
        
        if not search_words or not rawg_words:
            return False
        
        # 교집합 비율 계산
        common_words = search_words & rawg_words
        
        # 검색어 단어의 60% 이상이 RAWG 결과에 포함되면 매칭
        match_ratio = len(common_words) / len(search_words)
        
        # PUBG 특수 처리: "battlegrounds" 키워드
        if 'battlegrounds' in norm_search and 'battlegrounds' in norm_rawg:
            return True
        
        # Pokémon 특수 처리: pokemon + 버전명
        if 'pokemon' in norm_search and 'pokemon' in norm_rawg:
            # 버전 이름 중 하나라도 일치하면 OK
            version_words = {'scarlet', 'violet', 'sword', 'shield', 'diamond', 'pearl', 
                           'brilliant', 'shining', 'lets', 'go', 'pikachu', 'eevee',
                           'legends', 'arceus'}
            search_versions = search_words & version_words
            rawg_versions = rawg_words & version_words
            if search_versions & rawg_versions:
                return True
        
        return match_ratio >= 0.6
    
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
            
            # 추가 태그 (인기 F2P 게임용)
            ('hero-shooter', '히어로 슈터', 'genre'),
            ('ninja', '닌자', 'theme'),
            ('tank', '전차', 'theme'),
            ('vehicle', '탈것', 'feature'),
            ('combat', '전투', 'genre'),
            ('post-apocalyptic', '포스트 아포칼립스', 'theme'),
            ('dark-fantasy', '다크 판타지', 'theme'),
            ('mmo', 'MMO', 'feature'),
            ('mecha', '메카', 'theme'),
            ('destruction', '파괴', 'feature'),
            ('retro', '레트로', 'theme'),
            ('arcade', '아케이드', 'genre'),
            ('tactical-shooter', '택티컬 슈터', 'genre'),
            ('mythology', '신화', 'theme'),
        ]
        
        for slug, name, tag_type in required_tags:
            Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'tag_type': tag_type}
            )

