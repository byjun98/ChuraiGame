# 🗄️ ERD for GameMatch (ChuraiGame)

> **데이터베이스 스키마 문서**  
> **버전**: v2.0  
> **최종 수정일**: 2025-12-19

---

## 📋 목차

1. [추천 시스템 설계 철학](#추천-시스템-설계-철학)
2. [하이브리드 추천 구조](#하이브리드-추천-구조)
3. [테이블 관계 개요](#테이블-관계-개요)
4. [dbdiagram.io 코드](#dbdiagramio-코드)
5. [테이블 상세 설명](#테이블-상세-설명)
6. [인덱스 전략](#인덱스-전략)

---

## 추천 시스템 설계 철학

### 왜 게임(아이템) 기반 유사도인가?

| 비교 항목 | 유저 간 유사도 | 게임 간 유사도 (채택) |
|-----------|---------------|---------------------|
| **시간 복잡도** | O(U²) - 유저 수 제곱 | O(G²) - 게임 수 제곱 |
| **확장성** | 유저 증가 시 폭발적 증가 | 게임 수는 상대적으로 안정적 |
| **희소성** | 유저 벡터가 매우 희소 | 게임 벡터가 상대적으로 밀집 |
| **사전 계산** | 유저 변동 시 재계산 필요 | 게임 유사도는 캐싱 가능 |
| **실시간 성능** | 실시간 계산 어려움 | 조회 + 가중합으로 빠름 |

### 핵심 설계 결정

```
✅ users_gamesimilarity     → 게임 간 유사도 (추천 시스템의 핵심)
                              배치 작업으로 사전 계산, DB에 캐싱
                              
⚠️ 규칙: game_a_id < game_b_id (정규화 저장)
         → 저장 공간 50% 절약
         → unique index 의미 명확화

⚠️ users_usersimilarity    → 유저 간 유사도 (보조 용도)
                              SNS/팔로우 추천 등 제한적 사용
```

---

## 하이브리드 추천 구조

### 게임 벡터 = 여러 신호의 결합 (실무 표준)

```
❌ 잘못된 접근: "장르 벡터만으로 비교" → 거의 안 쓰임
⭕ 올바른 접근: 여러 신호를 가중합

┌─────────────────────────────────────────────────────────────────┐
│                    하이브리드 유사도 계산                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   final_similarity =                                            │
│       0.70 × collaborative_similarity   (GameSimilarity)       │
│     + 0.20 × genre_similarity           (Tag Jaccard)          │
│     + 0.10 × metacritic_similarity      (점수 차이)             │
│                                                                 │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│   │  GameRating      │  │      Tag          │  │ metacritic   │ │
│   │  (유저 평가)      │  │  (장르/테마)       │  │  _score      │ │
│   │                  │  │                  │  │              │ │
│   │  → 70% 가중치    │  │  → 20% 가중치    │  │  → 10% 가중치│ │
│   └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘ │
│            │                     │                   │         │
│            │      ┌──────────────┴───────────────────┘         │
│            │      │                                            │
│            ▼      ▼                                            │
│   ┌─────────────────────────────────────────┐                  │
│   │          GameSimilarity 테이블           │                  │
│   │   (협업필터링 유사도 사전 계산)           │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 평점 정규화 (비선형 → 선형)

| 원본 점수 | 정규화 값 | 설명 |
|-----------|----------|------|
| -1 | -1.0 | 역따봉 (싫어요) |
| 0 | 0.0 | 스킵 (모르겠음) |
| 3.5 | 0.7 | 따봉 (좋아요) |
| 5 | 1.0 | 쌍따봉 (최고!) |

### 추천 흐름

```
1. 유저 A가 좋아한 게임: [Game1: 5점, Game3: 3.5점]
   → 정규화: [Game1: 1.0, Game3: 0.7]

2. GameSimilarity 테이블 조회 (양방향):
   - Game1과 유사: Game7(0.9), Game12(0.8)
   - Game3과 유사: Game7(0.7), Game15(0.6)

3. 가중 점수 계산:
   - Game7:  (1.0×0.9 + 0.7×0.7) / (1.0 + 0.7) = 0.82
   - Game12: (1.0×0.8) / 1.0 = 0.80
   - Game15: (0.7×0.6) / 0.7 = 0.60

4. 최종 추천: Game7 > Game12 > Game15
```

---

## 테이블 관계 개요

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Users App                                           │
│                                                                                 │
│  ┌───────────────┐                                                              │
│  │    User       │◄─────────────────────┐                                       │
│  │               │                      │                                       │
│  │ - username    │    1:1               │                                       │
│  │ - steam_id    │◄────────┐            │                                       │
│  │ - nickname    │         │            │                                       │
│  └───────┬───────┘         │            │                                       │
│          │                 │            │                                       │
│    ┌─────┼─────────────────┼────────────┼──────────────────┐                    │
│    │     │                 │            │                  │                    │
│    ▼     ▼                 │            ▼                  ▼                    │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│ │SteamLibrary  │ │ Onboarding   │ │ UserSimilar  │ │  wishlist    │            │
│ │Cache         │ │ Status       │ │ ity (🆕)     │ │  (M:N)       │            │
│ │              │ │              │ │              │ │              │            │
│ │- library_data│ │- status      │ │- from_user   │ │- user_id     │            │
│ │- total_games │ │- total_rating│ │- to_user     │ │- game_id     │            │
│ │              │ │              │ │- sim_score   │ │              │            │
│ └──────────────┘ └──────────────┘ └──────────────┘ └──────┬───────┘            │
│                                                           │                     │
└───────────────────────────────────────────────────────────┼─────────────────────┘
                                                            │
┌───────────────────────────────────────────────────────────┼─────────────────────┐
│                              Games App                    │                      │
│                                                           ▼                      │
│  ┌──────────────┐                               ┌──────────────┐                │
│  │    Tag       │◄──────────────────────────────│    Game      │                │
│  │   (🆕)       │     M:N (games_game_tags)     │              │                │
│  │              │                               │ - title      │                │
│  │- name        │                               │ - genre      │ (레거시)       │
│  │- slug        │                               │ - metacritic │                │
│  │- tag_type    │                               │ - tags (M:N) │ (🆕)           │
│  │- weight      │                               └──────┬───────┘                │
│  └──────────────┘                                      │                        │
│                                                        │                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │                        │
│  │ Screenshot   │  │   Trailer    │  │   Rating     │◄─┤                        │
│  └──────────────┘  └──────────────┘  └──────────────┘  │                        │
│                                                        │                        │
│  ┌──────────────┐                                      │                        │
│  │ CachedGame   │                                      │                        │
│  │ List         │                                      │                        │
│  └──────────────┘                                      │                        │
│                                                        │                        │
└────────────────────────────────────────────────────────┼────────────────────────┘
                                                         │
┌────────────────────────────────────────────────────────┼────────────────────────┐
│                          Recommendation Layer          │                         │
│                                                        │                         │
│  ┌──────────────┐                             ┌────────┴─────────┐              │
│  │ GameRating   │                             │  GameSimilarity  │              │
│  │ (온보딩 평가) │─────────────────────────────▶│  (🔥 핵심)       │              │
│  │              │    배치 작업으로             │                  │              │
│  │- user_id     │    유사도 계산               │⚠️ game_a < game_b│              │
│  │- game_id     │                             │                  │              │
│  │- score       │  평점 정규화:                │- similarity_score│              │
│  │  -1/0/3.5/5  │  -1→-1.0, 3.5→0.7, 5→1.0   │- similarity_rank │ (🆕)         │
│  │              │                             │- calculated_at   │              │
│  └──────────────┘                             └──────────────────┘              │
│                                                                                  │
│  ※ GameSimilarity는 추천 시스템의 핵심 테이블                                    │
│  ※ 배치 작업(매일 새벽)으로 사전 계산하여 실시간 추천 성능 확보                    │
│  ※ similarity_rank로 Top-K 쿼리 최적화                                          │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
                                                           
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            Community App                                          │
│                                                                                  │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐             │
│  │    Post      │ 1:N     │   Comment    │  M:N    │  like_users  │             │
│  │              │────────▶│              │◄───────▶│              │             │
│  │- author      │         │- post_id     │         │- comment_id  │             │
│  │- title       │         │- author      │         │- user_id     │             │
│  │- content     │         │- content     │         │              │             │
│  │- category    │         └──────────────┘         └──────────────┘             │
│  └──────┬───────┘                                                               │
│         │                                                                        │
│         │ M:N                                                                    │
│         ▼                                                                        │
│  ┌──────────────┐                                                               │
│  │ post_like_   │                                                               │
│  │ users        │                                                               │
│  └──────────────┘                                                               │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## dbdiagram.io 코드

아래 코드를 [dbdiagram.io](https://dbdiagram.io)에 붙여넣어 시각적 ERD를 생성하세요.

```dbml
// ============================================================================
// GameMatch (ChuraiGame) Database Schema
// Version: 2.0
// Last Updated: 2025-12-19
// ============================================================================

// ============================================================================
// USERS APP - 사용자 관리, 인증, 추천 시스템
// ============================================================================

Table users_user {
  id integer [primary key, increment, note: '사용자 고유 ID']
  username varchar [unique, not null, note: '로그인용 사용자명']
  password varchar [not null, note: '해시된 비밀번호 (PBKDF2)']
  email varchar [unique, note: '이메일 주소']
  nickname varchar [note: '표시용 닉네임']
  avatar varchar [note: '프로필 이미지 경로']
  
  // Steam 연동
  steam_id varchar [unique, note: 'Steam 64bit ID']
  is_steam_linked boolean [default: false, note: 'Steam 연동 여부']
  
  // 기타 소셜 연동 (확장용)
  is_naver_linked boolean [default: false]
  is_google_linked boolean [default: false]
  
  // Django 기본 필드
  date_joined datetime [not null, note: '가입일']
  last_login datetime [note: '마지막 로그인']
  is_superuser boolean [default: false]
  is_staff boolean [default: false]
  is_active boolean [default: true]
  
  indexes {
    steam_id [name: 'idx_user_steam_id']
    email [name: 'idx_user_email']
  }
  
  note: '사용자 계정 정보. AbstractUser 확장'
}

Table users_steamlibrarycache {
  id integer [primary key, increment]
  user_id integer [ref: - users_user.id, not null, note: '1:1 관계']
  library_data json [note: 'Steam 라이브러리 게임 목록 JSON']
  total_games integer [default: 0, note: '보유 게임 수']
  total_playtime_hours float [default: 0, note: '총 플레이 시간']
  last_updated datetime [note: '마지막 갱신 시간']
  created_at datetime [note: '최초 생성 시간']
  
  note: 'Steam API 호출 최소화를 위한 캐시. 24시간 TTL'
}

Table users_gamerating {
  id integer [primary key, increment]
  user_id integer [ref: > users_user.id, not null]
  game_id integer [ref: > games_game.id, not null]
  score float [not null, note: '-1(역따봉), 0(스킵), 3.5(따봉), 5(쌍따봉)']
  is_onboarding boolean [default: false, note: '온보딩 중 평가 여부']
  created_at datetime [not null]
  updated_at datetime [not null]
  
  indexes {
    (user_id, game_id) [unique, name: 'idx_gamerating_user_game']
    (user_id, score) [name: 'idx_gamerating_user_score']
    (game_id, score) [name: 'idx_gamerating_game_score']
  }
  
  note: '온보딩 및 일반 게임 평가. 하이브리드 추천의 협업필터링 입력 데이터'
}

Table users_onboardingstatus {
  id integer [primary key, increment]
  user_id integer [ref: - users_user.id, not null, note: '1:1 관계']
  status varchar [not null, default: 'not_started', note: 'not_started/in_progress/completed/skipped']
  current_step integer [default: 0, note: '현재 온보딩 단계']
  total_ratings integer [default: 0, note: '총 평가 수']
  started_at datetime [note: '온보딩 시작 시간']
  completed_at datetime [note: '온보딩 완료 시간']
  
  note: '왓챠 스타일 온보딩 진행 상태 추적'
}

Table users_gamesimilarity {
  id integer [primary key, increment]
  game_a_id integer [ref: > games_game.id, not null, note: '⚠️ 항상 game_b_id보다 작은 ID']
  game_b_id integer [ref: > games_game.id, not null, note: '⚠️ 항상 game_a_id보다 큰 ID']
  similarity_score float [not null, note: '0~1 범위의 코사인 유사도']
  similarity_rank integer [not null, default: 0, note: '🆕 Top-K 쿼리 최적화용 순위']
  calculated_at datetime [not null, note: '계산 시점']
  
  indexes {
    (game_a_id, game_b_id) [unique, name: 'idx_similarity_games']
    (game_a_id, similarity_rank) [name: 'idx_similarity_game_a_rank']
    (game_b_id, similarity_rank) [name: 'idx_similarity_game_b_rank']
    (game_a_id, similarity_score) [name: 'idx_similarity_game_a_score']
    (game_b_id, similarity_score) [name: 'idx_similarity_game_b_score']
  }
  
  note: '🔥 추천 시스템 핵심 테이블\n⚠️ 규칙: game_a_id < game_b_id (저장 공간 50% 절약)\n📊 배치 작업으로 사전 계산된 협업필터링 유사도\n🚀 similarity_rank로 Top-K 쿼리 최적화'
}

Table users_usersimilarity {
  id integer [primary key, increment]
  from_user_id integer [ref: > users_user.id, not null]
  to_user_id integer [ref: > users_user.id, not null]
  similarity_score float [not null, default: 0, note: '0~1 범위의 유저 간 유사도']
  calculated_at datetime [not null, note: '계산 시점']
  
  indexes {
    (from_user_id, to_user_id) [unique]
    (from_user_id, similarity_score) [name: 'idx_usersim_from_score']
  }
  
  note: '⚠️ 보조 테이블 (게임 추천의 핵심 아님!)\n사용처: 취향 비슷한 유저 추천, SNS 팔로우 추천'
}

// User M:N 관계 테이블
Table users_user_wishlist {
  id integer [primary key, increment]
  user_id integer [ref: > users_user.id, not null]
  game_id integer [ref: > games_game.id, not null]
  
  indexes {
    (user_id, game_id) [unique]
  }
  
  note: '찜한 게임 목록'
}


// ============================================================================
// GAMES APP - 게임 정보, 태그, 캐시, 평점/리뷰
// ============================================================================

Table games_tag {
  id integer [primary key, increment]
  name varchar [not null, note: '태그명 (예: Action)']
  slug varchar [unique, not null, note: 'URL용 슬러그 (예: action)']
  tag_type varchar [not null, default: 'genre', note: 'genre/theme/feature/mood']
  weight float [not null, default: 1.0, note: '추천 계산 시 가중치']
  
  indexes {
    slug [name: 'idx_tag_slug']
    tag_type [name: 'idx_tag_type']
  }
  
  note: '🆕 게임 태그 (장르, 테마, 특징)\n하이브리드 추천에서 장르 유사도(20%) 계산에 사용'
}

Table games_game_tags {
  id integer [primary key, increment]
  game_id integer [ref: > games_game.id, not null]
  tag_id integer [ref: > games_tag.id, not null]
  
  indexes {
    (game_id, tag_id) [unique]
  }
  
  note: 'Game-Tag M:N 관계 중간 테이블'
}

Table games_game {
  id integer [primary key, increment]
  steam_appid integer [unique, note: 'Steam App ID (연동용)']
  rawg_id integer [note: 'RAWG API 게임 ID']
  title varchar [not null, note: '게임 제목']
  genre varchar [note: '⚠️ 레거시 장르 필드 (tags 사용 권장)']
  description text [note: '게임 설명 (향후 텍스트 임베딩용)']
  image_url varchar [note: '썸네일 이미지 URL']
  background_image varchar [note: '배경 이미지 URL']
  metacritic_score integer [note: '메타크리틱 점수 (0-100)\n하이브리드 추천에서 10% 가중치']
  
  indexes {
    steam_appid [name: 'idx_game_steam_appid']
    rawg_id [name: 'idx_game_rawg_id']
    metacritic_score [name: 'idx_game_metacritic']
  }
  
  note: '게임 기본 정보\n🎯 벡터화: 협업필터링(GameRating) + 태그(tags) + 메타스코어'
}

Table games_gamescreenshot {
  id integer [primary key, increment]
  game_id integer [ref: > games_game.id, not null]
  image_url varchar [not null, note: '스크린샷 URL']
  
  note: '게임 스크린샷 (RAWG API)'
}

Table games_gametrailer {
  id integer [primary key, increment]
  game_id integer [ref: > games_game.id, not null]
  name varchar [not null, note: '트레일러 제목']
  preview_url varchar [note: '미리보기 이미지']
  data_480 varchar [note: '480p 영상 URL']
  data_max varchar [note: '최고 해상도 영상 URL']
  
  note: '게임 트레일러 (RAWG API)'
}

Table games_cachedgamelist {
  id integer [primary key, increment]
  category varchar [unique, not null, note: 'popular/top_rated/new_releases/trending/upcoming']
  games_data json [not null, note: '게임 목록 JSON']
  updated_at datetime [not null, note: '캐시 갱신 시간']
  
  note: 'RAWG API 응답 캐시. 6시간 TTL로 98% 속도 향상'
}

Table games_rating {
  id integer [primary key, increment]
  user_id integer [ref: > users_user.id, not null]
  game_id integer [ref: > games_game.id, not null]
  score float [not null, note: '1.0 ~ 5.0 별점']
  content text [note: '리뷰 내용']
  playtime_forever integer [default: 0, note: 'Steam 플레이 시간 (분)']
  created_at datetime [not null]
  updated_at datetime [not null]
  
  indexes {
    (user_id, game_id) [unique, name: 'idx_rating_user_game']
  }
  
  note: '게임 평점 및 리뷰 (일반 리뷰, 온보딩과 별도)'
}


// ============================================================================
// COMMUNITY APP - 게시판, 댓글, 좋아요
// ============================================================================

Table community_post {
  id integer [primary key, increment]
  author_id integer [ref: > users_user.id, not null]
  category varchar [not null, note: '게시판 카테고리']
  title varchar [not null, note: '게시글 제목']
  content text [not null, note: '게시글 내용']
  image varchar [note: '첨부 이미지']
  video varchar [note: '첨부 영상']
  created_at datetime [not null]
  updated_at datetime [not null]
  
  note: '커뮤니티 게시글'
}

Table community_post_like_users {
  id integer [primary key, increment]
  post_id integer [ref: > community_post.id, not null]
  user_id integer [ref: > users_user.id, not null]
  
  indexes {
    (post_id, user_id) [unique]
  }
  
  note: '게시글 좋아요'
}

Table community_comment {
  id integer [primary key, increment]
  post_id integer [ref: > community_post.id, not null]
  author_id integer [ref: > users_user.id, not null]
  content text [not null]
  created_at datetime [not null]
  
  note: '게시글 댓글'
}

Table community_comment_like_users {
  id integer [primary key, increment]
  comment_id integer [ref: > community_comment.id, not null]
  user_id integer [ref: > users_user.id, not null]
  
  indexes {
    (comment_id, user_id) [unique]
  }
  
  note: '댓글 좋아요'
}


// ============================================================================
// TABLE GROUPS (dbdiagram.io 그룹핑)
// ============================================================================

TableGroup users_app [color: #3498db] {
  users_user
  users_steamlibrarycache
  users_gamerating
  users_onboardingstatus
  users_gamesimilarity
  users_usersimilarity
  users_user_wishlist
}

TableGroup games_app [color: #2ecc71] {
  games_tag
  games_game_tags
  games_game
  games_gamescreenshot
  games_gametrailer
  games_cachedgamelist
  games_rating
}

TableGroup community_app [color: #e74c3c] {
  community_post
  community_post_like_users
  community_comment
  community_comment_like_users
}
```

---

## 테이블 상세 설명

### Users App

| 테이블 | 목적 | 핵심 필드 | 비고 |
|--------|------|----------|------|
| `users_user` | 사용자 계정 | steam_id, nickname | AbstractUser 확장 |
| `users_steamlibrarycache` | Steam 라이브러리 캐시 | library_data (JSON) | 24시간 TTL |
| `users_gamerating` | 온보딩 평가 | score (-1/0/3.5/5) | **협업필터링 입력** |
| `users_onboardingstatus` | 온보딩 상태 | status, total_ratings | |
| `users_gamesimilarity` | **게임 유사도** ⭐ | similarity_score, **similarity_rank** | **핵심 테이블** |
| `users_usersimilarity` | 유저 유사도 (🆕) | similarity_score, calculated_at | 보조 용도 |
| `users_user_wishlist` | 찜 목록 | user_id, game_id | |

### Games App

| 테이블 | 목적 | 핵심 필드 | 비고 |
|--------|------|----------|------|
| `games_tag` | **태그** (🆕) | name, slug, tag_type, **weight** | **장르 유사도 계산** |
| `games_game_tags` | Game-Tag M:N | game_id, tag_id | |
| `games_game` | 게임 정보 | steam_appid, metacritic_score | **메타점수 유사도** |
| `games_gamescreenshot` | 스크린샷 | image_url | |
| `games_gametrailer` | 트레일러 | data_480, data_max | |
| `games_cachedgamelist` | API 캐시 | category, games_data (JSON) | 6시간 TTL |
| `games_rating` | 리뷰/평점 | score (1-5), content | 온보딩과 별도 |

### Community App

| 테이블 | 목적 | 핵심 필드 |
|--------|------|----------|
| `community_post` | 게시글 | title, content, category |
| `community_comment` | 댓글 | post_id, content |
| `community_post_like_users` | 게시글 좋아요 | post_id, user_id |
| `community_comment_like_users` | 댓글 좋아요 | comment_id, user_id |

---

## 인덱스 전략

### 추천 시스템 성능 최적화

```sql
-- GameSimilarity 테이블 인덱스 (🔥 핵심)
-- 정규화 저장: game_a_id < game_b_id
CREATE UNIQUE INDEX idx_similarity_games ON users_gamesimilarity (game_a_id, game_b_id);

-- Top-K 쿼리 최적화 (similarity_rank 사용)
CREATE INDEX idx_similarity_game_a_rank ON users_gamesimilarity (game_a_id, similarity_rank);
CREATE INDEX idx_similarity_game_b_rank ON users_gamesimilarity (game_b_id, similarity_rank);

-- 점수 기반 정렬 (폴백)
CREATE INDEX idx_similarity_game_a_score ON users_gamesimilarity (game_a_id, similarity_score DESC);
CREATE INDEX idx_similarity_game_b_score ON users_gamesimilarity (game_b_id, similarity_score DESC);

-- GameRating 테이블 인덱스
CREATE INDEX idx_gamerating_user_score ON users_gamerating (user_id, score);
CREATE INDEX idx_gamerating_game_score ON users_gamerating (game_id, score);

-- Tag 테이블 인덱스 (장르 유사도 계산용)
CREATE INDEX idx_tag_slug ON games_tag (slug);
CREATE INDEX idx_tag_type ON games_tag (tag_type);
```

### 쿼리 예시

```sql
-- Top-20 유사 게임 조회 (최적화된 쿼리)
-- similarity_rank 인덱스 사용 → 정렬 없이 조회
SELECT * FROM users_gamesimilarity 
WHERE (game_a_id = :game_id OR game_b_id = :game_id)
  AND similarity_rank <= 20;

-- 양방향 조회 (정규화된 스키마)
SELECT 
  CASE 
    WHEN game_a_id = :game_id THEN game_b_id 
    ELSE game_a_id 
  END AS similar_game_id,
  similarity_score
FROM users_gamesimilarity 
WHERE (game_a_id = :game_id OR game_b_id = :game_id)
  AND similarity_rank <= 20
ORDER BY similarity_score DESC;
```

---

## 📝 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2025-12-19 | 초기 작성 |
| **v2.0** | **2025-12-19** | **하이브리드 추천, Tag 모델, 정규화 저장, similarity_rank, UserSimilarity 추가** |

---

> **문서 작성**: SSAFY 13기 1학기 관통 프로젝트 팀
