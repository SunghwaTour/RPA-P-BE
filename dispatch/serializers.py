from rest_framework import serializers
from .models import Estimate

# 입력 데이터를 검증하기 위한 Serializer 클래스
class EstimateSerializer(serializers.Serializer):
    distance = serializers.IntegerField(required=True)  # 거리 (필수 입력값)
    departure_date = serializers.DateField(required=True)  # 출발 날짜 (필수 입력값)
    return_date = serializers.DateField(required=False, allow_null=True)  # 복귀 날짜 (선택 사항)
    kinds_of_estimate = serializers.CharField(required=True)  # 견적 종류 (왕복, 편도 등)
    is_accompany = serializers.BooleanField(required=True)  # 기사 동행 여부 (True/False)
    people_count = serializers.CharField(required=True)  # 인원 수 (문자열 형태)
