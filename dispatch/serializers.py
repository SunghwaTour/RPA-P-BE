from rest_framework import serializers
from .models import Estimate, EstimateAddress, Pay, VehicleInfo, VirtualEstimate, Review, ReviewFile
from django.db import transaction
from django.conf import settings

# 입력 데이터를 검증하기 위한 Serializer 클래스
class EstimatePriceSerializer(serializers.Serializer):
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

# 견적 신청 정보
class EstimateSerializer(serializers.ModelSerializer):
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

# 견적 상세 
class EstimateDetailSerializer(serializers.ModelSerializer):
    departure_address = serializers.CharField(source="departure.address")
    arrival_address = serializers.CharField(source="arrival.address")
    price = serializers.IntegerField(source="virtual_estimate.price", default=None)
    price_type = serializers.CharField(source="pay.price_type", default=None)
    depositor_name = serializers.CharField(source="pay.depositor_name", default=None)
    bus_type = serializers.CharField(source="vehicle_info.bus_type", default=None)
    bus_seater = serializers.CharField(source="vehicle_info.bus_seater", default=None)
    bus_count = serializers.IntegerField(source="vehicle_info.bus_count", default=None)

    class Meta:
        model = Estimate
        fields = [
            "created_date",  
            "status",
            "departure_date",
            "return_date",
            "departure_address",
            "arrival_address",
            "is_accompany",
            "people_count",
            "price",
            "price_type",
            "depositor_name",
            "bus_type",
            "bus_seater",
            "bus_count",
        ]

# 견적 리스트 조회
class EstimateListSerializer(serializers.ModelSerializer):
    departure_address = serializers.CharField(source="departure.address")
    arrival_address = serializers.CharField(source="arrival.address")
    finished_date = serializers.SerializerMethodField()
    price = serializers.IntegerField(source="virtual_estimate.price", default=None)

    class Meta:
        model = Estimate
        fields = [
            "id",
            "price",
            "status",
            "departure_address",
            "arrival_address",
            "departure_date",
            "return_date",
            "finished_date",
        ]
    
    def get_finished_date(self, obj):
        # finished_date가 None인 경우 빈 문자열 반환
        return obj.finished_date if obj.finished_date else ""

# 리뷰 파일
class ReviewFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewFile
        fields = ['file']

# 리뷰 등록 serializer
class ReviewSerializer(serializers.ModelSerializer):
    files = serializers.ListField(
        child=serializers.ImageField(),  # 파일 리스트 처리
        write_only=True,                # 입력 시에만 사용
        required=False                  # 필수 아님
    )

    class Meta:
        model = Review
        fields = ['estimate', 'star', 'detail', 'files']

    def create(self, validated_data):
        files = validated_data.pop('files', [])
        review = Review.objects.create(**validated_data)

        # 파일 저장
        for file in files:
            ReviewFile.objects.create(review=review, file=file)

        return review

    def validate(self, data):
        # 같은 사용자가 동일한 견적에 대해 리뷰를 작성했는지 확인
        user = self.context['request'].user
        estimate = data['estimate']
        
        if Review.objects.filter(estimate=estimate, user=user).exists():
            raise serializers.ValidationError("이미 이 견적에 대해 리뷰를 작성하셨습니다.")
        
        return data

# 리뷰 조회 serializer
class ReviewListSerializer(serializers.ModelSerializer):
    files = serializers.SerializerMethodField()
    bus_type = serializers.CharField(source="estimate.vehicle_info.bus_type", read_only=True)
    bus_seater = serializers.CharField(source="estimate.vehicle_info.bus_seater", read_only=True)
    departure_date = serializers.CharField(source="estimate.departure_date", read_only=True)
    return_date = serializers.CharField(source="estimate.return_date", read_only=True)
    purpose = serializers.CharField(source="estimate.purpose", read_only=True)

    class Meta:
        model = Review
        fields = [
            'id',
            'bus_type',  # 차량 종류
            'star',  # 평점
            'bus_seater',  # 좌석 수
            'departure_date',  # 출발 날짜짜
            'return_date',  # 도착 날짜
            'purpose',  # 목적
            'detail',  # 후기 텍스트
            'files'  # 이미지 리스트
        ]

    def get_files(self, obj):
        # 각 파일의 URL을 문자열 리스트로 반환
        return [f"{settings.MEDIA_URL}{file.file}" for file in obj.files.all()]

# 견적 수정 
class EstimateUpdateSerializer(serializers.ModelSerializer):
    bus_type = serializers.CharField(write_only=True, required=False)
    bus_count = serializers.IntegerField(write_only=True, required=False)
    price = serializers.IntegerField(write_only=True, required=False)
    status = serializers.CharField(required=False)  # Status 필드 추가

    class Meta:
        model = Estimate
        fields = ["bus_type", "bus_count", "price", 'status']

    def update(self, instance, validated_data):
        # 차량 정보 업데이트
        if "bus_type" in validated_data or "bus_count" in validated_data:
            if instance.vehicle_info:
                instance.vehicle_info.bus_type = validated_data.get("bus_type", instance.vehicle_info.bus_type)
                instance.vehicle_info.bus_count = validated_data.get("bus_count", instance.vehicle_info.bus_count)
                instance.vehicle_info.save()
            else:
                # VehicleInfo가 없는 경우 새로 생성
                instance.vehicle_info = VehicleInfo.objects.create(
                    bus_type=validated_data.get("bus_type", ""),
                    bus_count=validated_data.get("bus_count", 1)  # 기본값 1
                )

        # 가격 정보 업데이트
        if "price" in validated_data and instance.virtual_estimate:
            instance.virtual_estimate.price = validated_data.get("price", instance.virtual_estimate.price)
            instance.virtual_estimate.save()

        # 상태 정보 업데이트
        if "status" in validated_data:
            instance.status = validated_data.get("status", instance.status)

        # 저장 후 객체 반환
        instance.save()
        return instance
