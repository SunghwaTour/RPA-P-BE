from django.urls import path
from . import views 

urlpatterns = [
    path('register', views.RegisterView.as_view(), name='register'), # 회원가입
    path('login', views.LoginView.as_view(), name='login'), # 로그인
    path('refresh-token', views.RefreshTokenView.as_view(), name='refresh_token'), # 토큰 재발급
    path('send-code', views.SendCodeView.as_view(), name='send_code'), # 전화번호 인증 전송
    path('verify-code', views.VerifyCodeView.as_view(), name='verify_code'), # 전화번호 인증 확인
]