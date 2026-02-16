# 🎮 ChuraiGame (GameMatch)

> **Steam 연동 + 하이브리드 추천 + AI 큐레이션**으로 
> “지금 내 취향에 맞는 게임”을 빠르게 찾는 Django 기반 웹 서비스

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.16-ff1709?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-DB-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-2.3-013243?style=for-the-badge&logo=numpy&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-1.16-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white)
![scikit--learn](https://img.shields.io/badge/scikit--learn-1.8-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![Steam](https://img.shields.io/badge/Steam_OpenID-Integrated-000000?style=for-the-badge&logo=steam&logoColor=white)

</div>

---

## 1) 프로젝트 소개

ChuraiGame은 다음 3가지를 결합해 추천 품질과 체감 성능을 동시에 개선한 프로젝트입니다.

1. **Steam OpenID 로그인/연동**: 유저 라이브러리와 플레이 정보 연계
2. **하이브리드 추천 엔진**: 협업 필터링 + 태그(콘텐츠) + 메타크리틱 신호 결합
3. **외부 API 캐시 전략**: RAWG 호출을 DB 캐시로 흡수해 메인 진입 속도 개선

면접 포인트는 “기능 구현”보다, **외부 의존성을 어떻게 줄였고**, **데이터 스키마와 배치 계산을 어떻게 최적화했는지**입니다.

---

## 2) 기술 스택 (면접 답변용 핵심 위주)

### Backend
- **Django 5.2.8 + Django REST Framework 3.16.1**
- **SQLite** (로컬/개발 기준)
- 커스텀 유저 모델, 앱 분리(`users`, `games`, `community`)

### Data / Recommendation
- **pandas + NumPy + SciPy(sparse) + scikit-learn(cosine_similarity)**
- 평점 정규화 후 게임-유저 행렬 기반 **Item-based Collaborative Filtering**
- 게임 태그(장르/테마/특징/분위기) + 메타크리틱을 추가한 **Hybrid Similarity**

### External Integrations
- **Steam OpenID / Steam Web API**
- **RAWG API** (게임 상세/목록)
- CheapShark/기타 가격 데이터셋(JSON) 연동 구조

### Frontend
- Django Template 기반 렌더링 + 컴포넌트 템플릿 구조
- 정적 리소스/이미지 직접 서빙 구성

---

## 3) 아키텍처 요약

```text
Browser
  └─ Django Views / Template
       ├─ Users Domain (인증/온보딩/추천 진입)
       ├─ Games Domain (목록/상세/캐시/RAWG 연동)
       ├─ Community Domain (게시글/상호작용)
       └─ Recommendation Batch
            ├─ GameRating -> sparse matrix
            ├─ cosine similarity 계산
            └─ GameSimilarity Top-K 저장
```

---

## 4) 수치로 설명하는 개선 포인트 (면접용)

아래 수치는 코드 구조/정책 기준으로 설명 가능한 **구체 수치**입니다.

### 4-1. RAWG API 캐싱으로 외부 호출량 절감
- 캐시 단위: `popular`, `top_rated`, `trending`, `new_releases` 카테고리
- 카테고리별 기본 적재량: **40개**
- TTL: **6시간 이내 캐시 유효**

**개선 설명**
- 캐시 미적용 시: 메인 진입 때마다 카테고리별 외부 호출 반복
- 캐시 적용 시: TTL 구간 동안 **DB 조회로 대체**, 외부 호출 0회
- 한 번의 캐시 갱신 후 메인 진입 N회 동안, 호출량을 최대 **4N → 0**으로 줄이는 구조

### 4-2. 유사도 저장 스키마 최적화
- `game_a_id < game_b_id` 형태로 **정규화 저장**
- 동일 쌍(A,B)/(B,A) 중복 제거

**개선 설명**
- 페어 중복 제거로 유사도 저장 공간을 이론적으로 **약 50% 절감**
- `similarity_rank` 기반 Top-K 조회 최적화로 추천 시 후처리 비용 축소

### 4-3. 계산량 제어 파라미터화
- `--min-ratings`(기본 3), `--top-k`(기본 50), `--min-similarity`(기본 0.1)

**개선 설명**
- 평점이 적은 게임 제외로 노이즈/희소성 문제 완화
- 모든 페어를 저장하지 않고 상위 K만 유지하여 DB write/read 비용 통제

### 4-4. 온보딩 데이터 품질 필터
- JSON 온보딩 후보군에서 `steam_rating >= 75`, `review_count >= 500` 필터 적용
- 상위 **500개** 후보를 사용해 초기 평가 경험 구성

**개선 설명**
- 콜드스타트에서 “아는 게임이 너무 적게 보이는 문제”와 “품질 낮은 타이틀 노출”을 동시에 완화

---

## 5) 트러블슈팅 / 어려웠던 점 / 개선 방향

### A. 외부 API 의존으로 인한 체감 지연
**문제**
- 페이지 렌더 시 외부 API 직접 호출이 누적되면 응답 지연과 실패율 증가

**해결**
- `CachedGameList` 모델 기반 카테고리 캐시 + TTL + 수동 갱신 커맨드 분리

**다음 개선**
- 캐시 갱신을 주기 스케줄러(cron/celery beat)로 자동화
- 캐시 히트율/미스율 메트릭 수집(예: Prometheus)

### B. 추천 정확도 vs 계산 비용의 트레이드오프
**문제**
- 협업 필터링만 사용하면 신규/롱테일 게임에 취약
- 콘텐츠 신호를 늘리면 계산/관리 복잡도가 증가

**해결**
- 협업 + 태그 + 메타크리틱 가중합 하이브리드
- 배치 계산 시 sparse matrix 및 Top-K 컷오프 적용

**다음 개선**
- 가중치(협업/태그/메타) 자동 튜닝(A/B 테스트)
- 사용자 세그먼트별 가중치 동적 적용

### C. 데이터 소스 간 ID 불일치(Steam AppID vs RAWG ID)
**문제**
- 서로 다른 ID 체계 때문에 상세 이동/연결 시 누락 발생

**해결**
- 검색 리다이렉트 + 상세 뷰에서 다중 키(steam_appid/rawg_id/local id) 순차 탐색

**다음 개선**
- 통합 매핑 테이블을 별도 관리하고 동기화 배치 강화

---

## 6) 로컬 실행 가이드

### 요구사항
- Python 3.9+
- `.env`에 필요한 API 키 설정(RAWG 등)

### 설치
```bash
git clone <repo-url>
cd ChuraiGame
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 마이그레이션
```bash
python manage.py migrate
```

### 데이터/캐시 관련 커맨드
```bash
# 초기 게임 적재
python manage.py load_games

# 메인 목록 캐시 갱신
python manage.py refresh_game_cache

# 스팀 태그/리뷰 수집
python manage.py fetch_steam_tags
python manage.py fetch_steam_reviews

# 게임 간 유사도 배치 계산
python manage.py calculate_game_similarity --min-ratings 3 --top-k 50
```

### 실행
```bash
python manage.py runserver
```

---

## 7) 디렉터리 구조

```text
ChuraiGame/
├── ChuraiGame/                 # settings, urls
├── games/                      # 게임 도메인, RAWG 연동, 캐시, 상세
│   └── management/commands/    # load/cache/fetch 계열 배치
├── users/                      # 인증, Steam 연동, 온보딩, 추천
│   └── management/commands/    # 유사도 계산, 세일 동기화 등
├── community/                  # 커뮤니티 기능
├── templates/                  # 공통 템플릿
└── requirements.txt
```

---

## 8) 면접에서 이렇게 말하면 좋습니다 (요약)

- “외부 API 지연을 기능 문제로 보지 않고 **캐시 계층 문제**로 정의해서 해결했습니다.”
- “추천은 모델 성능만이 아니라 운영 비용도 중요해서, **Top-K 저장/정규화 스키마**로 트래픽 대비 비용을 줄였습니다.”
- “콜드스타트는 알고리즘 이전에 데이터 품질 이슈라서, 온보딩 후보군에 **평점/리뷰 수 필터**를 걸어 체감 추천 품질을 개선했습니다.”

