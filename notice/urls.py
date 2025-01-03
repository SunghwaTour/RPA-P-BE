from django.urls import path
from . import views

urlpatterns = [
    path('notices', views.NoticeList().as_view()),
]
