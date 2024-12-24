from django.urls import path
from . import views

urlpatterns = [
    path('estimates/approximate-price', views.EstimateView().as_view(), name='approximate-price'), # 견적 금액 리스트 조회
    path('estimates', views.EstimateView().as_view()), # 견적 신청
    path('estimates/<int:estimate_id>', views.EstimateDetailView().as_view()), # 견적 상세 조회, 
]
