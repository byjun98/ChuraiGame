"""
users 앱의 DRF Serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    사용자 정보 조회/수정용 Serializer
    """
    rated_games_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'steam_id',
            'is_onboarded',
            'rated_games_count',
            'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'rated_games_count']

    def get_rated_games_count(self, obj):
        from games.models import Rating
        return Rating.objects.filter(user=obj).count()


class UserCreateSerializer(serializers.ModelSerializer):
    """
    회원가입용 Serializer
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({
                'password': '비밀번호가 일치하지 않습니다.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user
