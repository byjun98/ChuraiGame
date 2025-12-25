# 🤖 AI 기능 코드 레퍼런스 (PPT 캡쳐용)

> 이 문서는 발표 PPT에 포함할 AI 관련 코드를 정리한 참고 자료입니다.

---

## 1. AI 게임 큐레이터 챗봇 (GPT-5 Nano)

### 📍 파일 위치
`users/views.py` - `ai_chat_api` 함수 (Line 584-822)

---

### 🎯 핵심 코드 1: 시스템 프롬프트

```python
# users/views.py (Line 689-721)

system_prompt_text = f"""당신은 '게임 큐레이터 AI'입니다. 게임 추천 전문가로서 다음 역할을 수행합니다:

🎮 **전문 분야**
- 모든 플랫폼(PC, 콘솔, 모바일)의 게임에 대한 깊은 지식
- 장르별 특성과 대표 게임들을 잘 알고 있음
- 최신 인기 게임과 숨겨진 명작까지 폭넓게 추천 가능
- Steam, Epic Games, PlayStation, Xbox, Nintendo 등 모든 플랫폼 게임 추천

📊 **추천 스타일**
- 유저의 취향과 플레이 스타일을 파악하여 맞춤 추천
- 게임의 장점, 특징, 플레이 시간, 난이도 등을 설명
- 이모지를 활용하여 친근하고 재미있게 대화

🚫 **중요: 추천 규칙**
1. 유저가 이미 평가하거나 보유한 게임은 새 게임 추천에서 **반드시 제외**합니다
2. 추천할 때 반드시 유저가 플레이/평가한 게임과 비교하며 설명해주세요:
   - "'{user_nickname}님이 좋아하신 OO 게임처럼 △△한 요소가 있어서..."
   - "OO 게임과 장르가 비슷하고, 스토리 전개 방식도 닮아있어요"
3. 유저의 선호 장르와 좋아하는 게임의 공통점을 분석해서 추천 이유를 구체적으로 설명
4. 유저가 싫어한 게임과 비슷한 장르/스타일은 피해주세요
5. 보유했지만 플레이타임이 짧은 게임이 있다면 마지막에 재추천

💡 **응답 규칙**
- 항상 한국어로 답변
- 게임 이름은 정확하게 표기 (원제 + 한글명 병기 권장)
- 1-5개 정도의 게임을 추천할 때는 번호 리스트로 정리
- 마지막에 추가 질문을 유도하는 문구 추가

{onboarding_context}
{steam_context}

사용자가 게임 외의 질문을 하면, 친절하게 게임 추천 관련 질문으로 유도해주세요."""
```

---

### 🎯 핵심 코드 2: 동적 컨텍스트 생성 (개인화)

```python
# users/views.py (Line 628-682)

# 1. 온보딩 및 평가 데이터 수집
from .models import GameRating
user_ratings = GameRating.objects.filter(user=user).select_related('game')

liked_games = []
disliked_games = []
genre_counts = {}

for rating in user_ratings:
    game = rating.game
    if rating.score >= 3.5:  # 따봉 이상
        liked_games.append(f"- {game.title} (⭐{rating.score})")
        # 장르 집계
        for g in game.genre.split(','):
            genre_counts[g.strip()] = genre_counts.get(g.strip(), 0) + 1
    elif rating.score <= 0:  # 역따봉
        disliked_games.append(f"- {game.title}")

top_genres = [k for k, v in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]]

onboarding_context = f"""
[평가 데이터]
- 선호 장르: {', '.join(top_genres)}
- 좋아한 게임: {', '.join(liked_games[:7])}
- 싫어한 게임: {', '.join(disliked_games[:5])}
"""

# 2. Steam 라이브러리 데이터 수집
if user.is_steam_linked:
    steam_library = get_steam_owned_games(user.steam_id)
    sorted_games = sorted(steam_library, key=lambda x: x.get('playtime_forever', 0), reverse=True)
    top_played = [f"{g['name']}({round(g['playtime_forever']/60, 1)}시간)" for g in sorted_games[:5]]
    
    steam_context = f"""
[Steam 라이브러리]
- 최다 플레이: {', '.join(top_played)}
- 보유 게임 수: {len(steam_library)}개
"""
```

---

### 🎯 핵심 코드 3: Gemini API 호출

```python
# users/views.py (Line 742-777)

# 1. 채팅 히스토리 변환 (OpenAI → Gemini 형식)
gemini_contents = []
for msg in chat_history[-10:]:
    role = "model" if msg.get('role') == 'assistant' else "user"
    gemini_contents.append({
        "role": role,
        "parts": [{"text": msg.get('content', '')}]
    })

# 2. 현재 메시지 추가
gemini_contents.append({
    "role": "user",
    "parts": [{"text": user_message}]
})

# 3. Payload 구성
payload = {
    "systemInstruction": {
        "parts": [{"text": system_prompt_text}]
    },
    "contents": gemini_contents,
    "generationConfig": {
        "temperature": 0.7,      # 창의성 조절
        "maxOutputTokens": 2048, # 응답 길이
        "topP": 0.8,
        "topK": 40
    }
}

# 4. API 호출
url = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

response = requests.post(
    url,
    params={'key': api_key},
    headers={'Content-Type': 'application/json'},
    json=payload,
    timeout=30
)

# 5. 응답 파싱
if response.status_code == 200:
    result = response.json()
    ai_text = result['candidates'][0]['content']['parts'][0]['text']
    return JsonResponse({'success': True, 'message': ai_text})
```

---

## 2. 실시간 번역 (Gemini 2.0 Flash Lite)

### 📍 파일 위치
- `users/views.py` - `translate_text_api` 함수 (Line 827-956)
- `games/utils.py` - `translate_text_gemini` 함수 (Line 188-233)

---

### 🎯 핵심 코드: 번역 프롬프트

```python
# users/views.py (Line 859-891)

prompt = f"""당신은 10년 경력의 전문 게임 로컬라이제이션 번역가입니다. 
수많은 AAA 타이틀과 인디 게임의 한국어화 작업을 담당해온 베테랑으로, 
게임 문화와 한국 게이머들의 언어 습관을 깊이 이해하고 있습니다.

🎮 **번역 전문 분야:**
- RPG, 액션, 어드벤처, 호러, 시뮬레이션 등 모든 장르
- 스팀, 플레이스테이션, Xbox, 닌텐도 등 모든 플랫폼
- 게임 스토리, UI 텍스트, 마케팅 문구

📜 **번역 원칙:**
1. **고유명사 보존**: 게임 타이틀, 캐릭터명, 지명, 아이템명 등은 원어 그대로 유지
   - 예: "Geralt of Rivia" → "리비아의 게랄트" (유명한 경우 한글화된 이름 사용)
   - 예: "Dark Souls" → "Dark Souls" (게임 타이틀은 그대로)

2. **게임 용어 현지화**: 한국 게이머들에게 익숙한 표현 사용
   - 예: "roguelike" → "로그라이크", "dungeon crawler" → "던전 크롤러"
   - 예: "open world" → "오픈 월드", "sandbox" → "샌드박스"

3. **자연스러운 한국어**: 번역투가 아닌 자연스러운 문장
   - 직역 금지, 의역을 통해 매끄러운 한국어로 표현
   - 한국어 어순과 표현에 맞게 재구성

4. **마케팅 톤 유지**: 원문의 흥미와 기대감을 살려서 번역
   - 게임의 분위기와 장르에 맞는 어조 사용
   - 호러는 긴장감 있게, 어드벤처는 설렘 있게

5. **출력 규칙**: 오직 번역된 텍스트만 출력. 설명, 주석, "번역:" 같은 라벨 없이 깔끔하게.

---
영어 원문:
{text}

한국어 번역:"""
```

---

### 🎯 번역 API 호출 코드

```python
# users/views.py (Line 893-911)

response = requests.post(
    f"https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={api_key}",
    headers={"Content-Type": "application/json"},
    json={
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    },
    timeout=30  # Gemini는 빨라서 30초면 충분
)

if response.status_code == 200:
    result = response.json()
    translated_text = result['candidates'][0]['content']['parts'][0]['text']
    return JsonResponse({
        'success': True,
        'translated': translated_text.strip()
    })
```

---

## 3. 추천 알고리즘 코드

### 📍 파일 위치
- `users/recommendation.py` - 추천 점수 계산
- `users/onboarding.py` - Item-Based CF
- `users/hybrid_similarity.py` - 하이브리드 유사도

---

### 🎯 핵심 코드 1: 추천 점수 계산

```python
# users/recommendation.py (Line 242-279)

def calculate_recommendation_score(game, user_genres, is_on_sale=False, sale_discount=0):
    """
    추천 점수 계산 (0-100)
    
    가중치 배분:
    1. 장르 매칭: 40점 (가장 중요)
    2. 메타크리틱: 25점 (품질 보장)
    3. 유저 평점: 20점
    4. 할인율: 15점 (부가 요소)
    """
    score = 0
    
    # 1. 장르 매칭 점수 (40점 만점)
    game_genres = [g.lower().replace(' ', '-') for g in game.get('genres', [])]
    if user_genres:
        genre_matches = sum(user_genres.get(g, 0) for g in game_genres)
        max_genre_score = max(user_genres.values()) if user_genres else 1
        genre_score = min(40, (genre_matches / max(max_genre_score, 1)) * 40)
        score += genre_score
    
    # 2. 메타크리틱 점수 (25점 만점)
    metacritic = game.get('metacritic') or 0
    if metacritic > 0:
        # 60-100점 범위를 0-25점으로 스케일링
        metacritic_score = min(25, max(0, (metacritic - 60) / 40 * 25))
        score += metacritic_score
    
    # 3. 유저 평점 (20점 만점)
    rating = game.get('rating', 0) or 0
    rating_score = (rating / 5) * 20
    score += rating_score
    
    # 4. 할인 보너스 (15점 만점)
    if is_on_sale:
        sale_score = min(15, (sale_discount / 100) * 15)
        score += sale_score
    
    return round(score, 1)
```

---

### 🎯 핵심 코드 2: Item-Based CF (코사인 유사도)

```python
# users/onboarding.py (Line 329-460)

from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

def calculate_game_similarity_batch(min_ratings=1, top_k=50, min_similarity=0.1):
    """
    배치 작업: 게임 간 유사도 계산
    - 희소 행렬로 메모리 효율화
    - 코사인 유사도 계산
    - 정규화된 스키마: game_a_id < game_b_id (저장 공간 50% 절약)
    """
    
    # 1. 평점 정규화 (비선형 → 선형)
    SCORE_NORMALIZATION = {-1: -1.0, 0: 0.0, 3.5: 0.7, 5: 1.0}
    df['normalized_score'] = df['score'].apply(lambda x: SCORE_NORMALIZATION.get(x, x / 5.0))
    
    # 2. 희소 행렬 생성 (게임 x 유저)
    sparse_matrix = csr_matrix(
        (scores, (game_codes, user_codes)),
        shape=(len(game_categories), len(user_categories))
    )
    
    # 3. 코사인 유사도 계산
    similarity_matrix = cosine_similarity(sparse_matrix)
    
    # 4. Top-K 유사 게임만 저장
    for i, game_x_id in enumerate(game_ids):
        sim_scores = similarity_matrix[i]
        sorted_indices = np.argsort(sim_scores)[::-1]  # 내림차순
        
        for rank, j in enumerate(sorted_indices[:top_k]):
            if i == j:
                continue
            score = sim_scores[j]
            if score < min_similarity:
                break
                
            # 정규화: 항상 작은 ID를 game_a로
            game_a_id = min(game_x_id, game_ids[j])
            game_b_id = max(game_x_id, game_ids[j])
            
            GameSimilarity.objects.create(
                game_a_id=game_a_id,
                game_b_id=game_b_id,
                similarity_score=score,
                similarity_rank=rank + 1
            )
```

---

### 🎯 핵심 코드 3: 하이브리드 유사도 (가중합)

```python
# users/hybrid_similarity.py (Line 28-32, 132-176)

# 가중치 설정
SIMILARITY_WEIGHTS = {
    'collaborative': 0.70,   # 협업 필터링 (가장 중요)
    'genre': 0.20,           # 장르/태그 유사도
    'metacritic': 0.10,      # 메타크리틱 점수 유사도
}

def calculate_hybrid_similarity(game_a, game_b, weights=None):
    """
    하이브리드 유사도 계산
    
    final_similarity = 
        0.70 * collaborative_similarity +
        0.20 * genre_similarity +
        0.10 * metacritic_similarity
    """
    weights = weights or SIMILARITY_WEIGHTS
    
    # 1. 협업 필터링 유사도 (GameSimilarity 테이블 조회)
    collab_sim = get_collaborative_similarity(game_a.id, game_b.id)
    
    # 2. 장르/태그 유사도 (Jaccard Index)
    genre_sim = calculate_genre_similarity(game_a, game_b)
    
    # 3. 메타크리틱 유사도 (점수 차이 기반)
    meta_sim = calculate_metacritic_similarity(
        game_a.metacritic_score, 
        game_b.metacritic_score
    )
    
    # 가중합 계산
    final_similarity = (
        weights.get('collaborative', 0.7) * collab_sim +
        weights.get('genre', 0.2) * genre_sim +
        weights.get('metacritic', 0.1) * meta_sim
    )
    
    return final_similarity, {
        'collaborative': collab_sim,
        'genre': genre_sim,
        'metacritic': meta_sim,
        'final': final_similarity
    }
```

---

### 🎯 핵심 코드 4: Jaccard Index (장르 유사도)

```python
# users/hybrid_similarity.py (Line 67-101)

def calculate_genre_similarity(game_a, game_b):
    """
    장르/태그 유사도 계산 (Jaccard Index)
    
    공식: |A ∩ B| / |A ∪ B|
    
    예시:
    - Game A: {action, rpg, adventure}
    - Game B: {action, rpg, shooter}
    - 교집합: {action, rpg} = 2
    - 합집합: {action, rpg, adventure, shooter} = 4
    - 유사도: 2/4 = 0.5
    """
    tags_a = set(game_a.tags.values_list('slug', flat=True))
    tags_b = set(game_b.tags.values_list('slug', flat=True))
    
    if not tags_a or not tags_b:
        return 0.0
    
    intersection = len(tags_a & tags_b)  # 교집합
    union = len(tags_a | tags_b)         # 합집합
    
    return intersection / union if union > 0 else 0.0
```

---

## 4. API 엔드포인트 정리

| 엔드포인트 | 메서드 | 기능 | 파일 |
|-----------|--------|------|------|
| `/users/ai-chat/` | POST | AI 게임 추천 챗봇 | `users/views.py` |
| `/users/translate/` | POST | 영→한 번역 | `users/views.py` |
| `/users/personalized-recommendations/` | GET | 개인화 추천 | `users/views.py` |
| `/users/onboarding/games/` | GET | 온보딩 게임 목록 | `users/urls.py` |
| `/users/onboarding/rate/` | POST | 게임 평가 | `users/urls.py` |
| `/users/steam/library/` | GET | Steam 라이브러리 | `users/views.py` |

---

## 5. 환경 변수 (API Keys)

```env
# .env 파일
STEAM_API_KEY=your_steam_api_key
RAWG_API_KEY=your_rawg_api_key
GMS_API_KEY=your_ssafy_gms_api_key  # GPT + Gemini 통합
```

---

## 📸 스크린샷 캡쳐 가이드

### PPT에 넣을 코드 스크린샷 추천

1. **시스템 프롬프트** (Line 689-721)
   - AI 페르소나 정의 부분
   - 동적 컨텍스트 주입 부분 (`{onboarding_context}`, `{steam_context}`)

2. **API 호출** (Line 742-777)
   - Gemini Native API 형식
   - `systemInstruction`, `generationConfig` 구조

3. **추천 점수 계산** (recommendation.py Line 242-279)
   - 가중치 배분 (40/25/20/15)
   - 점수 계산 로직

4. **코사인 유사도** (onboarding.py Line 391-399)
   - `csr_matrix` 생성
   - `cosine_similarity` 호출

5. **번역 프롬프트** (Line 859-891)
   - 전문 번역가 페르소나
   - 게임 용어 현지화 규칙

---

<div align="center">

**이 문서를 참고하여 PPT 슬라이드에 적절한 코드 스니펫을 캡쳐하세요!**

</div>
