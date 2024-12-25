from django.urls import path
from . import views

urlpatterns = [
    path('users/fcm-token', views.FCMTokenRegisterView.as_view(), name='register_fcm_token'),
    path('send-notification', views.SendNotificationView.as_view(), name='send-notification'),

]
