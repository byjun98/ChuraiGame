import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from .models import Rating, Game

def get_recommendations(user_id):
    # 1. DB에서 모든 평가 데이터 가져오기 (DataFrame 변환)
    ratings = Rating.objects.all().values('user_id', 'game_id', 'score')
    df = pd.DataFrame(ratings)
    
    # 2. Pivot Table 생성 (행: 유저, 열: 게임, 값: 점수)
    user_game_matrix = df.pivot_table(index='user_id', columns='game_id', values='score').fillna(0)
    
    # 3. 코사인 유사도 계산 (나와 다른 유저들 간의 유사도)
    user_similarity = cosine_similarity(user_game_matrix)
    user_sim_df = pd.DataFrame(user_similarity, index=user_game_matrix.index, columns=user_game_matrix.index)
    
    # 4. 나와 가장 유사한 유저 Top 5 추출
    similar_users = user_sim_df[user_id].sort_values(ascending=False)[1:6].index
    
    # 5. 그 유저들이 높게 평가했지만(4점 이상), 내가 아직 안 한 게임 추출
    # (상세 구현 생략)
    return recommended_game_ids