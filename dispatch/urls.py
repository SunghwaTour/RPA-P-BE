from django.urls import path
from . import views

urlpatterns = [
    path('estimates/approximate-price', views.EstimateView().as_view(), name='approximate-price'), # 견적 금액 리스트 조회회
]
