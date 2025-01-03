from django.db import models
from user.models import User
from django.conf import settings

# 출발지, 도착지, 경유지에 사용될 주소 정보
class EstimateAddress(models.Model):
    address = models.CharField(max_length=254)  # 위치 이름
    latitude = models.CharField(max_length=50)  # 위도
    longitude = models.CharField(max_length=50)  # 경도

    def __str__(self):
        return self.address


# 출발 및 복귀 날짜, 시간 정보
class EstimateTime(models.Model):
    date = models.CharField(max_length=10)  # Format: yyyy.MM.dd
    time = models.CharField(max_length=8)   # Format: HH:mm a

    def __str__(self):
        return f"{self.date} {self.time}"


# 결제 정보
class Pay(models.Model):
    PRICE_TYPE_CHOICES = [
        ("현금", "현금"),
        ("카드", "카드"),
        ("계좌이체", "계좌이체"),
    ]

    price_type = models.CharField(max_length=20, choices=PRICE_TYPE_CHOICES)  # 결제 방식
    depositor_name = models.CharField(max_length=255)  # 입금자 이름

    def __str__(self):
        return f"{self.price_type} - {self.depositor_name}"


# 차량 정보
class VehicleInfo(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ("우등", "우등"),
        ("일반", "일반"),
    ]

    bus_type = models.CharField(max_length=10, choices=VEHICLE_TYPE_CHOICES)  # 차량 유형
    bus_seater = models.CharField(max_length=10, default="45인승")  # 버스 좌석 수
    bus_count = models.IntegerField(default=1)  # 버스 대수

    def __str__(self):
        return f"{self.bus_type}, {self.bus_seater}, {self.bus_count}대"

class VirtualEstimate(models.Model):
    vehicle_types = models.ManyToManyField(VehicleInfo, related_name="virtual_estimates")
    price = models.IntegerField()  # 가격 정보

    def __str__(self):
        return f"Estimate ID: {self.id}, Price: {self.price}"



# 견적
class Estimate(models.Model):
    KINDS_OF_ESTIMATE_CHOICES = [
        ("왕복", "왕복"),
        ("편도", "편도"),
        ("셔틀", "셔틀"),
    ]

    STATUS_CHOICES = [
        ("업체 확인중", "업체 확인중"),
        ("계약금 입금 대기", "계약금 입금 대기"),
        ("예약 완료", "예약 완료"),
    ]

    PURPOSE_CHOICES = [
        ("워크샵", "워크샵"),
        ("통근/셔틀", "통근/셔틀"),
        ("단체관람", "단체관람"),
        ("결혼식", "결혼식"),
        ("골프", "골프"),
        ("기타", "기타"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Django가 설정한 사용자 모델 참조
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    kinds_of_estimate = models.CharField(max_length=10, choices=KINDS_OF_ESTIMATE_CHOICES)  # 견적 종류
    departure = models.ForeignKey(EstimateAddress, on_delete=models.CASCADE, related_name="departure_address")  # 출발지
    arrival = models.ForeignKey(EstimateAddress, on_delete=models.CASCADE, related_name="arrival_address")  # 도착지
    stopover = models.CharField(max_length=255, null=True, blank=True)  # 경유지 (텍스트로 저장)
    departure_date = models.DateTimeField()  # 출발 날짜 및 시간
    return_date = models.DateTimeField(null=True, blank=True)  # 복귀 날짜 및 시간 (선택 사항)
    people_count = models.IntegerField(null=True, blank=True)  # 인원 수
    pay = models.ForeignKey(Pay, on_delete=models.CASCADE, null=True, blank=True)  # 결제 정보
    virtual_estimate = models.ForeignKey(VirtualEstimate, on_delete=models.CASCADE, null=True, blank=True)  # 가견적 정보
    vehicle_info = models.ForeignKey(VehicleInfo, on_delete=models.CASCADE, null=True, blank=True)  # 차량 정보
    distance = models.IntegerField()  # 거리 (KM)
    is_dispatch_approval = models.BooleanField(default=False)  # 배차 확정 여부
    is_price_change = models.BooleanField(default=False)  # 가격 변경 여부
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="초기")  # 견적 상태
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default="기타")  # 견적 목적
    additional_requests = models.TextField(null=True, blank=True)  # 추가 요청 사항
    is_accompany = models.BooleanField(default=False)  # 기사 동행 여부
    created_date = models.DateTimeField(auto_now_add=True) # 견적 신청을 통해 객체 생성시의 시간
    is_finished = models.BooleanField(default=False)  # 완료 여부
    finished_date = models.DateField(null=True, blank=True)  # 완료 날짜 
    def __str__(self):
        return f"Estimate: {self.kinds_of_estimate}, Status: {self.status}"


# 리뷰 모델
class Review(models.Model) :
    estimate = models.ForeignKey(Estimate, on_delete=models.CASCADE, related_name="review_estimate")
    star = models.FloatField()
    detail = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# 리뷰 파일
class ReviewFile(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="files")
    file = models.ImageField(upload_to="review_files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)