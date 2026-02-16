diff --git a/README.md b/README.md
index 87224d00c0b6ed3e1d6fd48311b93df385f60141..01c1b220563c10ea6d3422deb23d3b47aa447476 100644
--- a/README.md
+++ b/README.md
@@ -1,191 +1,268 @@
-# 🎮 GameMatch (ChuraiGame)
+# 🎮 ChuraiGame (GameMatch)
 
-> **"당신의 취향, AI가 찾아드립니다."**
-> 
-> **Steam 연동 기반 하이브리드 게임 추천 & AI 큐레이팅 플랫폼**  
+> **Steam 연동 + 온보딩 평가 + 하이브리드 추천 + Gemini 기반 AI 큐레이션**
+>
+> “무슨 게임 하지?”를 데이터로 해결하는 개인화 게임 추천 서비스
 
 <div align="center">
 
 ![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
 ![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
-![Vue.js](https://img.shields.io/badge/Vue.js-3.0-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)
-![Steam](https://img.shields.io/badge/Steam_API-Intergration-000000?style=for-the-badge&logo=steam&logoColor=white)
-![OpenAI](https://img.shields.io/badge/GPT--5_Nano-AI_Curator-412991?style=for-the-badge&logo=openai&logoColor=white)
-![Google Gemini](https://img.shields.io/badge/Gemini_2.0-Translator-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white)
+![DRF](https://img.shields.io/badge/DRF-3.16-red?style=for-the-badge&logo=django&logoColor=white)
+![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)
+![SQLite](https://img.shields.io/badge/SQLite-DB-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
+![Steam](https://img.shields.io/badge/Steam-OpenID%2FWebAPI-000000?style=for-the-badge&logo=steam&logoColor=white)
+![RAWG](https://img.shields.io/badge/RAWG-GameData-6A5ACD?style=for-the-badge)
+![CheapShark](https://img.shields.io/badge/CheapShark-SaleData-1E90FF?style=for-the-badge)
+![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash%20Lite-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white)
 
 </div>
 
-<br>
+---
+
+## 1) 프로젝트 소개
 
-## 📖 프로젝트 개요
+**ChuraiGame**은 아래 3가지 데이터 소스를 합쳐 개인화 추천을 제공하는 프로젝트입니다.
 
-**GameMatch**는 "할 게임이 없다"고 느끼는 게이머들을 위해 개발되었습니다.  
-단순한 인기 순위가 아닌, **사용자의 Steam 라이브러리 플레이 기록**과 **직관적인 온보딩 평가**를 분석하여 개인화된 게임을 추천합니다.
+1. **Steam 라이브러리**(보유 게임, 플레이 타임)
+2. **온보딩 평가 데이터**(초기 선호/비선호)
+3. **외부 메타데이터**(RAWG 평점·장르, CheapShark 할인 정보)
 
-### 💡 핵심 가치
-- **Connectivity**: Steam 계정 연동 한 번으로 나의 게임 인생을 분석
-- **Personalization**: 플레이 타임과 평가 데이터를 결합한 정교한 추천 알고리즘
-- **Optimization**: 외부 API 의존도를 낮추고 자체 캐싱 시스템으로 **98% 속도 향상**
-- **Intelligence**: GPT-5 기반 AI 큐레이터와의 대화를 통한 감성 추천
+핵심은 “인기 게임 나열”이 아니라, **취향 벡터 + 품질 점수 + 할인 가치**를 함께 반영하는 것입니다.
 
 ---
 
-## 🏗 시스템 아키텍처
+## 2) 기술 스택 (면접 포인트 중심)
+
+### Backend
+- **Django 5.2.8 + Django REST Framework 3.16.1**
+- **SQLite** (개발/학습 단계에서 빠른 실험 목적)
+- **Custom User Model** + Steam OpenID 연동
+- 데이터 파이프라인성 작업은 **Management Command**로 분리
+
+### Data / ML
+- **Pandas / NumPy / SciPy / scikit-learn**
+- `csr_matrix` + `cosine_similarity` 기반 **Item-Based CF**
+- 평점 스케일 정규화: `-1, 0, 3.5, 5` → `-1.0 ~ 1.0`
+
+### External Integration
+- **Steam Web API / OpenID 2.0**: 사용자 식별 + 라이브러리 조회
+- **RAWG API**: 메타데이터(장르/평점/이미지/설명)
+- **CheapShark API**: 세일/역대 최저가
+- **Gemini API (GMS 경유)**: AI 추천 챗 + 번역
+
+### Frontend
+- Django Template 내부에서 **Vue 3** 컴포넌트 스타일 UI 구성
+
+---
+
+## 3) 아키텍처 요약
 
 ```mermaid
 graph TD
-    User[User / Browser] -->|Vue.js Interaction| Frontend[Frontend Views]
-    Frontend -->|REST API| Backend[Django REST Framework]
-    
-    subgraph "Backend Service"
-        Backend -->|Auth| SteamAuth[Steam OpenID Login]
-        Backend -->|Feature| Recommender[Recommendation Engine]
-        Backend -->|Feature| AIChat[AI Chatbot (GPT/Gemini)]
-        Backend -->|Data| DB[(SQLite DB)]
-        
-        Recommender -->|Read| CachedGame[DB Cache Layer]
-        Recommender -->|Calc| Similarity[SciPy Hybrid Filtering]
-    end
-    
-    subgraph "External APIs"
-        SteamAuth --> SteamAPI[Steam Web API]
-        Backend --> RAWG[RAWG Game API]
-        Backend --> CheapShark[CheapShark Sale API]
-        AIChat --> OpenAI[GPT-5 Nano]
-    end
-    
-    CachedGame -.->|Cache Miss| RAWG
+    U[User] --> V[Vue in Django Template]
+    V --> B[Django/DRF]
+
+    B --> A1[Steam OpenID + Web API]
+    B --> A2[RAWG API]
+    B --> A3[CheapShark API]
+    B --> A4[Gemini API]
+
+    B --> DB[(SQLite)]
+    DB --> C1[CachedGameList]
+    DB --> C2[GameRating / GameSimilarity]
 ```
 
 ---
 
-## ⚡ 기술적 도전과 해결 (Troubleshooting)
-
-### 1. RAWG API 속도 문제 해결 (Performance Optimization)
-**문제:** 메인 페이지 로딩 시 `Popular`, `Trending`, `New Release` 등의 섹션을 위해 매번 RAWG API를 호출하여 로딩 시간이 **9초 이상** 소요됨.  
-**해결:**
-- **DB Caching Layer** 구현: API 응답 결과를 `CachedGameList` 모델에 JSON 형태로 저장.
-- **TTL (Time-To-Live)** 설정: 6시간 주기로 자동 갱신.
-- **결과:** 로딩 속도 **9초 → 0.15초 (약 98% 단축)** 달성.
-
-### 2. Cold Start 문제 해결 (Onboarding System)
-**문제:** 신규 가입자는 데이터가 없어 추천이 불가능함.  
-**해결:** 
-- **왓챠(Watcha) 스타일 온보딩** 도입.
-- 가입 직후 인기 게임 1,500개를 스와이프하며 평가 (-1: 싫어요, 0: 관심없음, 3.5: 좋아요, 5: 인생게임).
-- 최소 3개 이상 평가 시 즉시 **Item-Based Collaborative Filtering** 작동.
-
-### 3. 추천 정교화 (Hybrid Recommendation)
-**전략:** 단순히 장르만 매칭하지 않고 복합적인 점수 산정 로직 구현.
-```python
-# games/recommendation.py
-def calculate_score(game, user_pref):
-    score = 0
-    score += genre_match_score(game) * 0.4  # 장르 적합도 (40%)
-    score += metacritic_score(game) * 0.25  # 전문가 평점 (25%)
-    score += user_rating_score(game) * 0.2  # 유저 평점 (20%)
-    score += sale_benefit_score(game) * 0.15 # 할인율 (15%)
-    return score
-```
+## 4) 핵심 기능
+
+### 4-1. Steam 기반 개인화 추천
+- Steam 연동 시 보유 게임/플레이타임 기반 선호 장르 추출
+- 플레이타임 가중치 반영(분 단위 데이터 활용)
+- 이미 보유한 게임 제외 로직 적용
+
+### 4-2. 콜드스타트 대응 온보딩
+- 리뷰/평점 기준으로 정제된 상위 게임군에서 평가 진행
+- 최소 평가 데이터가 쌓이면 CF 계산으로 전환
+- Steam 미연동 유저도 온보딩 기반 추천 가능
+
+### 4-3. 하이브리드 점수 기반 추천
+- 장르 적합도 + 메타크리틱 + 유저 평점 + 할인율 가중 합산
+- 점수 기준 정렬로 설명 가능한 추천 결과 생성
+
+### 4-4. AI 큐레이터
+- 최근 대화 히스토리와 사용자 컨텍스트를 결합한 프롬프트 구성
+- “이미 보유했지만 플레이 적은 게임”까지 추천 문맥에 반영
+
+### 4-5. 세일 인텔리전스
+- CheapShark 페이징 수집 + 재시도/딜레이로 안정성 확보
+- 평점/리뷰 수 조건 기반 필터로 저품질 딜 노이즈 축소
 
 ---
 
-## ✨ 주요 기능 상세
+## 5) 트러블슈팅 & 수치 개선 (면접에서 말하기 좋은 항목)
+
+### A. RAWG 호출 병목 최적화
+**문제**
+- 추천 생성 시 외부 API 호출이 과도하면 응답 지연이 커짐.
+
+**개선**
+- 추천 후보 수집 order를 3개(`-metacritic`, `-rating`, `-added`)로 제한.
+- 각 요청 `page_size=40`, `max_pages=1`로 고정.
 
-### 1. 🔐 Steam 완벽 연동
-- **OpenID 2.0**: 보안 걱정 없는 공식 로그인 지원
-- **라이브러리 분석**: 보유 게임, 플레이 타임 자동 동기화
-- **실시간 반영**: "내가 어제 3시간 플레이한 Elden Ring"이 즉시 추천 알고리즘에 반영됨
+**수치 포인트**
+- 코드 주석 기준: **112회 호출 → 3회 호출** 구조로 축소(약 **97.3% 감소**).
+- 이론상 외부 후보 최대 **120개(=40×3)**로 bounded 처리.
 
-### 2. 🤖 AI 게임 큐레이터 (Chatbot)
-- **Context-Aware**: 단순 챗봇이 아닙니다. 유저의 Steam 라이브러리와 평가 데이터를 Prompt Context로 주입.
-- **GPT-5 Nano**: "너 엘든링 100시간 했네? 그럼 P의 거짓은 어때?" 같은 개인화된 대화 가능.
-- **Gemini Translation**: 영어로 된 게임 설명을 Gemini 2.0 Flash Lite를 이용해 1초 만에 자연스러운 한국어로 번역.
+---
+
+### B. 메인 화면 캐시 레이어 도입
+**문제**
+- 메인 탭(인기/트렌딩/신작 등) 진입마다 RAWG 재호출 시 느림 + API 의존도 증가.
 
-### 3. 💰 스마트 세일 정보
-- **CheapShark API Integration**: Steam 외에도 다양한 스토어의 최저가 비교.
-- **Scam Filter**: 할인율은 높지만 평점이 낮은 '스컴 게임'을 자동 필터링 (리뷰 500개 이상, 긍정 80% 이상).
+**개선**
+- `CachedGameList`에 카테고리별 JSON 저장.
+- `max_age_hours=6` TTL 캐시 사용.
+- `refresh_game_cache` 커맨드로 사전 워밍/갱신.
 
-### 4. 👥 커뮤니티 & 리뷰
-- 게임별 별점 평가 및 코멘트 작성
-- 유저 간 게시글 작성, 좋아요, 댓글 소통 기능
-- 이미지 업로드 지원
+**수치 포인트**
+- 카테고리별 기본 **40개** 캐시.
+- TTL 내에서는 네트워크 호출 없이 DB 응답.
 
 ---
 
-## 🛠 설치 및 실행 방법
+### C. CF 저장 구조 최적화
+**문제**
+- 게임-게임 유사도는 쌍(pair) 데이터가 빠르게 커짐.
+
+**개선**
+- `(game_a_id, game_b_id)`를 항상 `a < b`로 정규화 저장.
+- 중복쌍 제거 후 Top-K 랭크만 유지.
+
+**수치 포인트**
+- 설계상 저장쌍 **약 50% 절감**.
+- 기본 파라미터: `min_ratings=3`, `top_k=50`, `min_similarity=0.1`.
+
+---
+
+### D. 온보딩 품질 필터링
+**문제**
+- 콜드스타트 단계에서 저품질/표본 부족 게임이 많으면 평가 신뢰도가 낮아짐.
+
+**개선**
+- 온보딩 풀 생성 시 `steam_rating >= 75`, `review_count >= 500` 필터 적용.
+- 상위 **500개**를 후보군으로 유지해 다양성 확보.
+
+**수치 포인트**
+- 카드 페이지네이션: 기본 `per_page=8`.
+- 평가 데이터 부족 시 최소 수집 기준 기반으로 추천 전략 전환.
+
+---
+
+### E. AI 응답 안정성 제어
+**문제**
+- 장문 컨텍스트/무제한 히스토리로 비용·지연·파싱 불안정 발생 가능.
+
+**개선**
+- 최근 히스토리 **최대 10개 메시지**만 사용.
+- `maxOutputTokens=2048`, API timeout 30초로 안전장치 설정.
+
+**수치 포인트**
+- 컨텍스트 길이와 응답 길이를 상한선으로 통제해 실패율 완화.
+
+---
+
+## 6) 어려웠던 점 / 배운 점
+
+1. **도메인 문제**: 게임명 매칭이 단순 문자열로는 부정확함(동명·스핀오프·에디션 문제).
+2. **데이터 문제**: Steam/RAWG/CheapShark 간 식별자 불일치로 정합성 이슈 발생.
+3. **제품 문제**: 추천 정확도 vs 응답 속도의 트레이드오프를 동시에 맞추는 게 가장 어려웠음.
+4. **운영 문제**: 외부 API rate limit, timeout, 결측치 대응이 기능 구현보다 더 많은 시간을 차지.
+
+---
+
+## 7) 앞으로의 개선 방향
+
+### 7-1. 데이터/모델
+- SQLite → PostgreSQL 전환 + 인덱스/쿼리 플랜 튜닝
+- 추천 품질 오프라인 평가 지표 도입(Precision@K, Recall@K, NDCG)
+- 장르 텍스트 기반 임베딩(설명/태그) 결합해 hybrid 고도화
+
+### 7-2. 서비스 안정성
+- 캐시 계층 확장(DB 캐시 + Redis)
+- 배치 파이프라인 스케줄링(Celery/cron) 표준화
+- 외부 API 실패 시 fallback 정책(서킷브레이커/백오프) 고도화
+
+### 7-3. 사용자 경험
+- 추천 이유(why)와 근거 feature를 UI에 더 명시적으로 노출
+- 온보딩 질문 동적화(응답 패턴에 따라 다음 카드 난이도/장르 조정)
+- A/B 테스트로 추천 탭 전환율·체류시간 측정
+
+---
+
+## 8) 로컬 실행 방법
 
 ### Prerequisites
 - Python 3.9+
-- Django 5.x
-- API Keys (RAWG, OpenAI/GMS)
+- `.env` (예: `RAWG_API_KEY`, `GMS_API_KEY` 등)
 
-### 1. 환경 설정
+### 설치
 ```bash
-# Repository Clone
-git clone https://github.com/username/ChuraiGame.git
+git clone <repo_url>
 cd ChuraiGame
-
-# 가상환경 생성 및 실행
-python -m venv venv
-source venv/bin/activate  # Windows: venv\Scripts\activate
-
-# 패키지 설치
+python -m venv .venv
+source .venv/bin/activate  # Windows: .venv\Scripts\activate
 pip install -r requirements.txt
 ```
 
-### 2. 데이터베이스 초기화 (필수)
-이 프로젝트는 대량의 게임 데이터를 다루므로 초기 적재 과정이 필요합니다.
-
+### 초기화
 ```bash
-# DB 마이그레이션
 python manage.py migrate
-
-# 1. 게임 기본 데이터 적재 (JSON -> DB)
 python manage.py load_games
-
-# 2. 장르 정보 업데이트 (RAWG API 연동, 약 10~20분 소요)
-python manage.py update_genres --limit=100  # 테스트용 100개만 우선 실행 권장
-
-# 3. 메인 페이지용 캐시 생성 (속도 향상 핵심)
 python manage.py refresh_game_cache
+```
 
-# 4. 게임 유사도 계산 (Item-Based CF 추천용, 평가 데이터 필요)
-python manage.py calculate_game_similarity
-# 옵션: --min-ratings 5 (최소 5개 평가받은 게임만), --top-k 30 (상위 30개 유사 게임 저장)
+### 선택 배치
+```bash
+python manage.py calculate_game_similarity --min-ratings 3 --top-k 50
+python manage.py update_steam_sales --delay 1.0
+python manage.py fetch_steam_reviews --limit=100 --reviews=10
+python manage.py cache_translations --limit=50
 ```
 
-### 3. 서버 실행
+### 실행
 ```bash
 python manage.py runserver
 ```
-접속: [http://localhost:8000](http://localhost:8000)
 
 ---
 
-## 📂 폴더 구조 (Project Structure)
+## 9) 프로젝트 구조
 
-```
+```text
 ChuraiGame/
-├── games/                  # 게임 데이터, 추천 로직, API 관리
-│   ├── management/commands # 데이터 적재/싱크 스크립트
-│   ├── utils.py            # RAWG API 래퍼 & 추천 알고리즘
-│   └── views.py            # 게임 상세, API 뷰
-├── users/                  # 유저 관리, Steam 연동, 온보딩
-│   ├── steam_auth.py       # Steam OpenID & API 핸들러
-│   ├── onboarding.py       # 왓챠 스타일 평가 로직
-│   └── views.py            # AI 챗봇, 프로필
-├── community/              # 게시판 기능
-├── templates/              # Vue.js가 포함된 Django 템플릿
-└── steamsale.py            # 세일 데이터 크롤링 모듈
+├── ChuraiGame/                  # Django settings/urls
+├── users/                       # 인증, Steam 연동, 온보딩, 추천, AI 채팅
+│   └── management/commands/     # 유사도/세일/데이터 배치 커맨드
+├── games/                       # 게임 모델, 캐시, RAWG/번역/리뷰 처리
+│   └── management/commands/
+├── community/                   # 게시글/댓글 등 커뮤니티 기능
+├── templates/                   # Django base template
+└── img/                         # 정적 이미지 리소스
 ```
 
 ---
 
-<div align="center">
+## 10) 면접에서 1분 요약용 멘트
 
-**Created by SSAFY 14기 1학기 관통 프로젝트 팀**
-<br>
-사용된 모든 게임 이미지의 저작권은 각 개발사/배급사에 있습니다.
+> “ChuraiGame은 Steam 데이터와 온보딩 평가를 결합한 하이브리드 추천 서비스입니다. 
+> 핵심 개선은 외부 API 병목을 줄인 것으로, 추천 후보 수집 호출을 112회에서 3회로 줄여 응답 경계를 명확히 만들었고, 
+> 메인 페이지는 6시간 TTL 캐시로 API 의존도를 낮췄습니다. 
+> 또 게임 유사도는 희소행렬+코사인 유사도로 계산하고 `a<b` 정규화 저장으로 pair 저장량을 약 50% 절감했습니다.”
 
+---
+
