from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model() # settings.py에서 설정한 모델을 가져옵니다.

# 1. 회원가입 폼 (Create)
class SignupForm(UserCreationForm):
    # 유효성 검사(비밀번호 일치, 아이디 중복 등)는 UserCreationForm이 다 해줍니다.
    # 우리는 추가로 받고 싶은 필드만 정의하면 됩니다.
    
    nickname = forms.CharField(
        label="닉네임",
        max_length=50,
        error_messages={
            'required': '닉네임을 입력해주세요.'
        }
    )
    
    email = forms.EmailField(
        label="이메일",
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # 폼에 입력받을 필드들 순서
        fields = ('username', 'email', 'nickname') 

# 2. 로그인 폼 (Read/Auth)
class CustomLoginForm(AuthenticationForm):
    # 디자인을 위해 위젯 속성 추가 (placeholder 등)
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '아이디'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '비밀번호'})
    )