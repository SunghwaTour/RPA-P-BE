from django.db import models

# 출발지, 도착지, 경유지에 사용될 주소
class EstimateAddress(models.Model):
    name = models.CharField(max_length=255)  # 위치 이름
    latitude = models.CharField(max_length=50)  # 위도
    longitude = models.CharField(max_length=50)  # 경도

    def __str__(self):
        return self.name

# 출발 및 복귀 날짜, 시간 정보
class EstimateTime(models.Model):
    date = models.CharField(max_length=10)  # Format: yyyy.MM.dd
    time = models.CharField(max_length=8)   # Format: HH:mm a

    def __str__(self):
        return f"{self.date} {self.time}"

# 결제 정보
class Pay(models.Model):
    PAY_WAY_CHOICES = [
        ("현금", "현금"),
        ("카드", "카드"),
        ("계좌이체", "계좌이체"),
    ]

    pay_way = models.CharField(max_length=20, choices=PAY_WAY_CHOICES)  # 결제 방식
    signed_name = models.CharField(max_length=255)  # 서명된 이름

    def __str__(self):
        return f"{self.pay_way} - {self.signed_name}"

# 차량 종류
class VehicleType(models.Model):
    name = models.CharField(max_length=50)  # 차량 종류 이름

    def __str__(self):
        return self.name

# 운행 종류
class OperationType(models.Model):
    name = models.CharField(max_length=50)  # 운행 종류 이름

    def __str__(self):
        return self.name

# 가견적 정보
class VirtualEstimate(models.Model):
    no = models.IntegerField()  # 견적 번호
    vehicle_types = models.ManyToManyField(VehicleType, related_name="virtual_estimates")  # 차량 종류
    operation_types = models.ManyToManyField(OperationType, related_name="virtual_estimates")  # 운행 종류
    price = models.IntegerField()  # 가격 정보

    def __str__(self):
        return f"Estimate No: {self.no}, Price: {self.price}"

# 메인 견적
class Estimate(models.Model):
    KINDS_OF_ESTIMATE_CHOICES = [
        ("왕복", "왕복"),
        ("편도", "편도"),
        ("셔틀", "셔틀"),
    ]

    kinds_of_estimate = models.CharField(max_length=10, choices=KINDS_OF_ESTIMATE_CHOICES)  # 견적 종류
    departure = models.ForeignKey(EstimateAddress, on_delete=models.CASCADE, related_name="departure")  # 출발지
    return_address = models.ForeignKey(EstimateAddress, on_delete=models.CASCADE, related_name="return_address")  # 도착지
    stopover = models.ForeignKey(EstimateAddress, on_delete=models.SET_NULL, related_name="stopover", null=True, blank=True)  # 경유지
    departure_date = models.ForeignKey(EstimateTime, on_delete=models.CASCADE, related_name="departure_date")  # 출발 날짜 및 시간
    return_date = models.ForeignKey(EstimateTime, on_delete=models.CASCADE, related_name="return_date", null=True, blank=True)  # 복귀 날짜 및 시간
    number = models.IntegerField(null=True, blank=True)  # 인원 수
    pay = models.ForeignKey(Pay, on_delete=models.SET_NULL, null=True, blank=True)  # 결제 정보
    virtual_estimate = models.ForeignKey(VirtualEstimate, on_delete=models.SET_NULL, null=True, blank=True)  # 가견적 정보
    is_dispatch_approval = models.BooleanField(default=False)  # 배차 확정 여부
    is_price_change = models.BooleanField(default=False)  # 가격 변경 여부

    def __str__(self):
        return f"Estimate: {self.kinds_of_estimate}, Departure: {self.departure}, Return: {self.return_address}"
