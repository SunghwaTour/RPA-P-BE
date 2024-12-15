from django.urls import path
from . import views

urlpatterns = [
    path('register-token', views.FCMTokenRegisterView.as_view(), name='register_fcm_token'),
    # path('send-notification', views.SendPushNotificationView.as_view(), name='send_push_notification'),
]
