"""
users 앱의 REST API Views
Vue.js 프론트엔드와 통신하는 API 엔드포인트
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserCreateSerializer
from .recommendation import get_personalized_recommendations

User = get_user_model()


class SignupView(generics.CreateAPIView):
    """
    회원가입 API
    POST /api/auth/signup/
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    현재 사용자 정보 조회/수정 API
    GET /api/auth/user/
    PATCH /api/auth/user/
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """
    로그아웃 API - Refresh Token 블랙리스트
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'detail': '로그아웃되었습니다.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LinkSteamView(APIView):
    """
    Steam 계정 연동 API
    POST /api/auth/link-steam/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        steam_id = request.data.get('steam_id')
        if not steam_id:
            return Response(
                {'detail': 'Steam ID가 필요합니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        user.steam_id = steam_id
        user.save()
        
        return Response({
            'detail': 'Steam 계정이 연동되었습니다.',
            'steam_id': steam_id
        })


class SteamLibraryView(APIView):
    """
    Steam 라이브러리 조회 API
    GET /api/auth/steam-library/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.steam_id:
            return Response(
                {'detail': 'Steam 계정이 연동되지 않았습니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Steam API 호출하여 라이브러리 조회
        # 현재는 DB에 저장된 게임 목록 반환
        from games.models import Game
        owned_games = Game.objects.filter(owners=user)
        
        return Response({
            'count': owned_games.count(),
            'games': [
                {
                    'id': game.id,
                    'name': game.name,
                    'image': game.image_url
                }
                for game in owned_games[:50]
            ]
        })


class RecommendationsView(APIView):
    """
    맞춤 추천 게임 API
    GET /api/auth/recommendations/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        try:
            recommendations = get_personalized_recommendations(user, limit=20)
            return Response({
                'count': len(recommendations),
                'results': recommendations
            })
        except Exception as e:
            return Response(
                {'detail': f'추천을 가져오는데 실패했습니다: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OnboardingView(APIView):
    """
    온보딩 데이터 저장/조회 API
    GET /api/auth/onboarding/
    POST /api/auth/onboarding/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # 온보딩에서 평가한 게임 목록 반환
        from games.models import Rating
        ratings = Rating.objects.filter(user=user)
        
        return Response({
            'is_onboarded': user.is_onboarded,
            'rated_games_count': ratings.count(),
            'ratings': [
                {
                    'game_id': r.game.id,
                    'game_name': r.game.name,
                    'score': r.score
                }
                for r in ratings
            ]
        })

    def post(self, request):
        user = request.user
        ratings_data = request.data.get('ratings', [])
        
        from games.models import Game, Rating
        
        created_count = 0
        for rating_data in ratings_data:
            game_id = rating_data.get('game_id')
            score = rating_data.get('score')
            
            try:
                game = Game.objects.get(id=game_id)
                Rating.objects.update_or_create(
                    user=user,
                    game=game,
                    defaults={'score': score}
                )
                created_count += 1
            except Game.DoesNotExist:
                continue
        
        # 온보딩 완료 표시
        user.is_onboarded = True
        user.save()
        
        return Response({
            'detail': f'{created_count}개의 게임 평가가 저장되었습니다.',
            'is_onboarded': True
        })
