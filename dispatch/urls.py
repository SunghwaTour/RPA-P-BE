from django.urls import path
from . import views

urlpatterns = [
    path('estimates/approximate-price', views.EstimatePriceView().as_view(), name='approximate-price'), # 견적 금액 리스트 조회
    path('estimates', views.EstimateView().as_view()), # 견적 신청(POST), 견적 리스트 조회(GET)
    path('estimates/<int:estimate_id>', views.EstimateDetailView().as_view()), # 견적 상세 조회(GET), 견적 삭제(DELETE) # trp에서 받은 정보에 대한 견적 수정(PATCH)
    path('estimates/confirm', views.EstimateStatusUpdateView().as_view()), # 견적 예약 확정(PATCH)

    path('estimates/review', views.ReviewView().as_view()), # 리뷰 등록(POST)
    path('estimates/reviews', views.ReviewListView().as_view()), # 리뷰 조회

    path('manual_scheduler', views.EstimateNotificationScheduler.as_view(), name='manual_scheduler'), # 테스트용 알림

]
