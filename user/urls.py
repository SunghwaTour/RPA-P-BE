from django.urls import path
from . import views 

urlpatterns = [
    path('login', views.UserManagementView.as_view(), name='login'), # 로그인 or 회원가입
    path('refresh-token', views.RefreshTokenView.as_view(), name='refresh_token'), # 토큰 재발급
    path('codes', views.SendCodeView.as_view(), name='send_code'), # 전화번호 인증 전송
    path('codes/verify', views.VerifyCodeView.as_view(), name='verify_code'), # 전화번호 인증 확인
]