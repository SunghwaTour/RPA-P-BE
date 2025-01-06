from django.urls import path
from . import views

urlpatterns = [
    path('users/fcm-token', views.FCMTokenRegisterView.as_view(), name='register_fcm_token'),
    path('notification', views.TestNotificationView.as_view()), # 알림 테스트
]
