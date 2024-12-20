from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from rest_framework.permissions import AllowAny
from .serializers import EstimateSerializer

# 견적 금액 조회
class EstimateView(APIView):
    permission_classes = [AllowAny]  

    # 금액을 계산하는 메서드
    def calculate_price(self, distance, kinds_of_estimate, is_weekday, is_peak_season, is_accompany, days):
        BASIC_PRICE_UNDER_100KM = 500000  # 100km 이하의 기본 요금
        BASIC_PRICE_OVER_100KM = 692000   # 100km 초과 시 기본 요금
        WAITING_TIME_PRICES = [150000, 90000, 30000, 0]  # 대기 시간에 따른 운임 비용 (구간별 0~400km)
        PRICE_PER_KM_200_TO_400 = 3460  # 200~400km 구간의 km당 요금
        PRICE_PER_KM_OVER_400 = 2590    # 400km 초과 구간의 km당 요금
        ADDITIONAL_CHARGES = {
            "weekday": 150000,         # 평일 추가 요금
            "peak_season": 200000,     # 성수기 추가 요금
            "daily_extra": 692000,     # 하루 추가 시 추가 요금
            "driver": 150000,          # 기사 동행 추가 요금
            "one_way_discount": 0.8    # 편도 운행 시 할인율 (20% 할인)
        }

        # 대기 시간 비용을 계산
        def get_waiting_time_price(distance):
            if distance < 200:
                return WAITING_TIME_PRICES[0]
            elif distance < 300:
                return WAITING_TIME_PRICES[1]
            elif distance < 400:
                return WAITING_TIME_PRICES[2]
            else:
                return WAITING_TIME_PRICES[3]

        # 거리 초과 비용을 계산
        def get_distance_price(distance):
            if distance < 200:
                return 0
            elif distance < 400:
                return (distance - 200) * PRICE_PER_KM_200_TO_400
            else:
                return (200 * PRICE_PER_KM_200_TO_400) + (distance - 400) * PRICE_PER_KM_OVER_400

        # 기본 요금 결정
        basic_price = BASIC_PRICE_UNDER_100KM if distance <= 100 else BASIC_PRICE_OVER_100KM
        waiting_time_price = get_waiting_time_price(distance)  # 대기 시간 비용 계산
        distance_price = get_distance_price(distance)  # 거리 초과 비용 계산

        # 총 비용 계산
        total_price = basic_price + waiting_time_price + distance_price

        # 조건에 따른 요금 조정
        if kinds_of_estimate == "편도":
            total_price *= ADDITIONAL_CHARGES["one_way_discount"]  # 편도 할인 적용
        if is_weekday:
            total_price += ADDITIONAL_CHARGES["weekday"]  # 평일 요금 추가
        if is_peak_season:
            total_price += ADDITIONAL_CHARGES["peak_season"]  # 성수기 요금 추가
        if days > 1:
            total_price += ADDITIONAL_CHARGES["daily_extra"] * (days - 1)  # 추가 일수에 대한 요금 추가
        if is_accompany:
            total_price += ADDITIONAL_CHARGES["driver"]  # 기사 동행 요금 추가

        return int(total_price)  # 최종 요금 반환

    def post(self, request):
        serializer = EstimateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  
        data = serializer.validated_data

        # 입력 데이터
        distance = data["distance"]  # 거리 정보
        departure_date = data["departure_date"]  # 출발 날짜
        return_date = data.get("return_date") or ""  # 복귀 날짜 (없으면 빈 문자열)
        kinds_of_estimate = data["kinds_of_estimate"]  # 견적 종류
        is_accompany = data["is_accompany"]  # 기사 동행 여부
        people_count = data["people_count"]  # 인원 수

        # 날짜 및 조건 계산
        days = 1  # 기본 운행 일수
        if return_date:  # 복귀 날짜가 있을 경우 출발일과 복귀일의 차이 계산
            return_date_parsed = datetime.strptime(str(return_date), "%Y-%m-%d")
            departure_date_parsed = datetime.strptime(str(departure_date), "%Y-%m-%d")
            days = (return_date_parsed - departure_date_parsed).days + 1

        is_weekday = departure_date.weekday() < 5  # 평일 여부 확인
        is_peak_season = departure_date.month in [4, 5, 9, 10]  # 성수기 여부 확인

        # 일반 및 우등 버스 요금 계산
        regular_price = self.calculate_price(distance, kinds_of_estimate, is_weekday, is_peak_season, is_accompany, days)
        luxury_price = regular_price + 150000  # 우등 버스 추가 요금 적용

        # 추천 버스 대수 및 좌석 정보 계산
        recommended_seater = "45인승"  # 기본 추천 좌석
        recommended_bus_count = 1  # 기본 버스 대수

        if people_count != "미정" and people_count.isdigit():  # 인원이 숫자일 경우 버스 대수 계산
            if int(people_count) > 45:
                recommended_bus_count = (int(people_count) + 44) // 45  # 버스 대수 계산 (45명 기준)

        # 응답 데이터 구성
        response_data = {
            "recommended_seater": recommended_seater,  # 추천 좌석
            "recommended_bus_count": str(recommended_bus_count),  # 추천 버스 대수
            "price_list": [
                {"price": str(regular_price), "bus_type": "일반"},  # 일반 버스 가격
                {"price": str(luxury_price), "bus_type": "우등"}   # 우등 버스 가격
            ]
        }

        return Response({"data": response_data})  
