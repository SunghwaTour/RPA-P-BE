from rest_framework import serializers
from .models import Estimate, EstimateAddress, Pay, VehicleInfo, VirtualEstimate
from django.db import transaction

# 입력 데이터를 검증하기 위한 Serializer 클래스
class EstimateSerializer(serializers.Serializer):
    distance = serializers.IntegerField(required=True)  # 거리 (필수 입력값)
    departure_date = serializers.DateField(required=True)  # 출발 날짜 (필수 입력값)
    return_date = serializers.DateField(required=False, allow_null=True)  # 복귀 날짜 (선택 사항)
    kinds_of_estimate = serializers.CharField(required=True)  # 견적 종류 (왕복, 편도 등)
    is_accompany = serializers.BooleanField(required=True)  # 기사 동행 여부 (True/False)
    people_count = serializers.CharField(required=True)  # 인원 수 (문자열 형태)

# 출발지, 도착지에 대한 정보
class EstimateAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstimateAddress
        fields = ["address", "latitude", "longitude"]

# 결제 방법에 대한 정보
class PaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pay
        fields = ["price_type", "depositor_name"]

# 버스에 대한 정보
class VehicleInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleInfo
        fields = ["bus_type", "bus_seater", "bus_count"]

# 가견적에 대한 정보
class VirtualEstimateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VirtualEstimate
        fields = ["price"]

# 견적 정보
class EstimateSaveSerializer(serializers.ModelSerializer):
    departure = EstimateAddressSerializer()
    arrival = EstimateAddressSerializer()
    pay = PaySerializer()
    vehicle_info = VehicleInfoSerializer()
    virtual_estimate = VirtualEstimateSerializer()

    class Meta:
        model = Estimate
        fields = [
            "departure",
            "arrival",
            "stopover",
            "departure_date",
            "return_date",
            "kinds_of_estimate",
            "distance",
            "pay",
            "vehicle_info",
            "virtual_estimate",
            "is_accompany",
            "purpose",
            "additional_requests",
            "people_count",
        ]

    def create(self, validated_data):
        try:
            with transaction.atomic():  # 중간에 오류 시 DB에 일부만 저장되는거 방지
                departure_data = validated_data.pop("departure")
                arrival_data = validated_data.pop("arrival")
                pay_data = validated_data.pop("pay", None)
                vehicle_data = validated_data.pop("vehicle_info")
                virtual_estimate_data = validated_data.pop("virtual_estimate")

                departure = EstimateAddress.objects.create(**departure_data)
                arrival = EstimateAddress.objects.create(**arrival_data)
                pay = Pay.objects.create(**pay_data) if pay_data else None
                vehicle_info = VehicleInfo.objects.create(**vehicle_data)

                # 가견적 저장
                virtual_estimate = VirtualEstimate.objects.create(price=virtual_estimate_data["price"])
                virtual_estimate.vehicle_types.add(vehicle_info)

                # 기본 상태 설정
                validated_data["status"] = "업체 확인중"

                # Estimate 생성
                estimate = Estimate.objects.create(
                    departure=departure,
                    arrival=arrival,
                    pay=pay,
                    vehicle_info=vehicle_info,
                    virtual_estimate=virtual_estimate,
                    **validated_data
                )
                return estimate
        except Exception as e:
            raise serializers.ValidationError(f"An error occurred: {str(e)}")