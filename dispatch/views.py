from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from rest_framework.permissions import AllowAny
from .serializers import EstimateSerializer, EstimateDetailSerializer, EstimateListSerializer, EstimatePriceSerializer
from rest_framework import status
from .models import Estimate
from django.db import transaction
from django.core.paginator import Paginator
from urllib.parse import urlencode

# 견적 금액 조회
class EstimatePriceView(APIView):
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
        serializer = EstimatePriceSerializer(data=request.data)
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

# 견적 신청(POST), 견적 리스트 조회(GET)
class EstimateView(APIView):
    
    # 견적 신청
    def post(self, request):
        serializer = EstimateSerializer(data=request.data)
        if serializer.is_valid():
            # 저장, 견적 객체 가져오기
            estimate = serializer.save(user=request.user)

            # RPA-D 관리자 알림

            # TRP 서버에 견적 등록

            response_data = {
                "data": {
                    "status": estimate.status 
                }
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        # 유효하지 않은 데이터 처리
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # 견적 조회
    def get(self, request):
        # 쿼리 파라미터 가져오기
        page = request.query_params.get("page", 1)
        is_finished = request.query_params.get("is_finished")

        # 필터링
        estimates = Estimate.objects.filter(user=request.user)
        if is_finished == "true":
            estimates = estimates.filter(is_finished=True)
        elif is_finished == "false":
            estimates = estimates.filter(is_finished=False)

        # 페이징 처리
        paginator = Paginator(estimates, 10)  # 페이지당 10개
        try:
            current_page = paginator.page(page)
        except:
            return Response({
                "result": "false",
                "message": "유효하지 않은 페이지 번호입니다."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 직렬화
        serializer = EstimateListSerializer(current_page.object_list, many=True)
        
        # URL 생성
        base_url = request.build_absolute_uri('?')
        next_url = (
            f"{base_url}{urlencode({'page': current_page.next_page_number(), 'is_finished': is_finished})}"
            if current_page.has_next() else None
        )
        previous_url = (
            f"{base_url}{urlencode({'page': current_page.previous_page_number(), 'is_finished': is_finished})}"
            if current_page.has_previous() else None
        )

        # response 데이터 
        response_data = {
            "result": "true",
            "message": "견적 리스트 조회 성공",
            "data": {
                "count": paginator.count,
                "next": next_url,
                "previous": previous_url,
                "estimates": serializer.data,
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)

# 견적 상세 조회(GET), 견적 삭제(DELETE)
class EstimateDetailView(APIView):
    # 견적 상세 조회
    def get(self, request, estimate_id):
        # Estimate 객체 가져오기
        try:
            estimate = Estimate.objects.get(id=estimate_id, user=request.user)
        except Estimate.DoesNotExist:
            return Response({
                'result': 'false',
                'message': '해당 ID의 견적을 찾을 수 없거나 내가 작성한 견적이 아닙니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # serializer를 통해 데이터 직렬화
        serializer = EstimateDetailSerializer(estimate)
        
        # 반환 값
        response_data = {
            'result': 'true',
            'message': '견적 상세 조회에 성공했습니다.',
            'data': serializer.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

    # 견적 삭제
    def delete(self, request, estimate_id):
        try:
            # 견적 객체 가져오기
            estimate = Estimate.objects.get(id=estimate_id)
            
            # 트랜잭션 처리로 데이터 삭제
            with transaction.atomic():
                estimate.delete()
            
            return Response({
                "result": "true",
                "message": "견적이 성공적으로 삭제되었습니다."
            }, status=status.HTTP_200_OK)
        
        except Estimate.DoesNotExist:
            return Response({
                "result": "false",
                "message": "해당 ID의 견적이 존재하지 않습니다."
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                "result": "false",
                "message": f"오류가 발생했습니다: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

