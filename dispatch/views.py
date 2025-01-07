from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime
from rest_framework.permissions import AllowAny
from .serializers import EstimateSerializer, EstimateDetailSerializer, EstimateListSerializer, EstimatePriceSerializer, ReviewSerializer, ReviewListSerializer, EstimateUpdateSerializer
from rest_framework import status
from .models import Estimate, Review
from django.db import transaction
from django.core.paginator import Paginator
from urllib.parse import urlencode
from rest_framework.generics import ListAPIView
from config.pagination import Pagination
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from firebase.models import FCMToken
from firebase.send_message import send_notification
from my_settings import ALLOWED_HOSTS, DEV4_SERVER , DEV_SERVER
from django.http import HttpResponseForbidden

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
    def post(self, request):
        serializer = EstimateSerializer(data=request.data)
        if serializer.is_valid():
            # 저장, 견적 객체 생성
            estimate = serializer.save(user=request.user)

            # RPA-D 서버 알림 API 호출
            rpad_url = f"{DEV4_SERVER}/user/notification"
            notification_data = {
                "title": "새 견적 신청 알림",
                "content": f"새로운 견적이 신청되었습니다. 견적 ID: {estimate.id}",
                "category": "일정",
                "send_datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }

            try:
                rpad_response = requests.post(rpad_url, json=notification_data)

                if rpad_response.status_code != 201:
                    return Response({
                        "result": "false",
                        "message": "견적 신청 성공, 그러나 알림 발송 실패 (RPA-D)"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                return Response({
                    "result": "false",
                    "message": f"알림 발송 중 오류 발생 (RPA-D): {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


            # TRP 서버에 견적 데이터 전송 추가
            trp_url = f"{DEV4_SERVER}/dispatch/estimates"  # TRP 서버 URL

            trp_payload = {
                "estimate_id": estimate.id,

                "departure": estimate.departure.address if estimate.departure and estimate.departure.address else "",
                "arrival": estimate.arrival.address if estimate.arrival and estimate.arrival.address else "",
                "departure_date": estimate.departure_date.strftime('%Y-%m-%d %H:%M:%S') if estimate.departure_date else "",
                "arrival_date": estimate.return_date.strftime('%Y-%m-%d %H:%M:%S') if estimate.return_date else "",
                "bus_cnt": estimate.vehicle_info.bus_count if estimate.vehicle_info and estimate.vehicle_info.bus_count else 0,
                
                "bus_type": estimate.vehicle_info.bus_type if estimate.vehicle_info and estimate.vehicle_info.bus_type else "",
                "customer": estimate.user.username if estimate.user and estimate.user.username else "",
                "customer_phone": estimate.user.phone_number if estimate.user and estimate.user.phone_number else "",
                "price": estimate.virtual_estimate.price if estimate.virtual_estimate and estimate.virtual_estimate.price else 0,
                "distance": estimate.distance if estimate.distance else 0,
                
                "payment_method": estimate.pay.price_type if estimate.pay and estimate.pay.price_type else "",
                "operation_type": estimate.kinds_of_estimate if estimate.kinds_of_estimate else "",
                "references": f"{estimate.stopover if estimate.stopover else ''} / {estimate.additional_requests if estimate.additional_requests else ''}".strip("/"),
                "route": f"{estimate.departure.address if estimate.departure else ''} > {estimate.arrival.address if estimate.arrival else ''}".strip(">"),
                # 추가적으로 RPAP에 없는 필드 처리
                "contract_status": "보류",
                "reservation_company": "성화투어",
                "operating_company": "성화투어",
                "driver_allowance": 0,
                "cost_type": "",

                "bill_place": "",
                "collection_type": "",
                "VAT": "y",
                "total_price": 0,
                "ticketing_info": "",
                
                "order_type": "",
                "driver_lease": "",
                "vehicle_lease": "",

                "time": "0",

                "night_work_time": "0",
                "distance_list": "",
                "time_list": "",
                "option" : "",
            }


            try:
                trp_response = requests.post(trp_url, json=trp_payload)

                if trp_response.status_code != 201:
                    return Response({
                        "result": "false",
                        "message": "견적 신청 성공, 그러나 TRP 데이터 전송 실패 : {trp_response.text}"
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                return Response({
                    "result": "false",
                    "message": f"TRP 데이터 전송 중 오류 발생: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 최종 응답
            return Response({
                "result": "true",
                "message": "견적 신청 성공",
                "data": {"status": estimate.status}
            }, status=status.HTTP_201_CREATED)

        # 데이터 검증 실패
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
    
    
    # trp에서 수정된 정보들 저장
    permission_classes = [AllowAny]  
    ALLOWED_IPS = ALLOWED_HOSTS  # 허용할 IP 목록
  
    def patch(self, request, estimate_id):
        client_ip = self.get_client_ip(request)
        if client_ip not in self.ALLOWED_IPS:
            return HttpResponseForbidden("Access denied: Unauthorized IP")
        
        try:
            # estimate_id를 기반으로 해당 견적 찾기
            estimate = Estimate.objects.get(id=estimate_id)
        except Estimate.DoesNotExist:
            return Response({
                "result": "false",
                "message": "해당 견적을 찾을 수 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)

        # Partial 업데이트를 위해 데이터 전달
        serializer = EstimateUpdateSerializer(estimate, data=request.data, partial=True)
        if serializer.is_valid():
            # 데이터 저장
            updated_estimate = serializer.save()

            # 변화 여부 저장
            updated_estimate.is_value_changed = True
            updated_estimate.save()

            return Response({
                "result": "true",
                "message": "견적이 성공적으로 수정되었습니다.",
                "data": {
                    "status": updated_estimate.status
                }
            }, status=status.HTTP_200_OK)

        # 유효성 검사 실패 시 에러 반환
        return Response({
            "result": "false",
            "message": "입력 데이터가 유효하지 않습니다.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


# 리뷰 등록(POST)
class ReviewView(APIView):
    # 리뷰 등록
    def post(self, request):
        serializer = ReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                "result": True,
                "message": "리뷰가 성공적으로 등록 되었습니다."
            }, status=status.HTTP_201_CREATED)

        return Response({
            "result": False,
            "message": "리뷰 등록 중 오류가 발생했습니다.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 리뷰 조회
class ReviewListView(ListAPIView):
    queryset = Review.objects.all().order_by('-created_at')  # 최신순 정렬
    serializer_class = ReviewListSerializer
    pagination_class = Pagination

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "result": "true",
            "message": "리뷰 목록 조회 성공",
            "data": response.data
        })   

# 10, 14시마다 유저에게는 입금 요청 알림을, 관리자에게는 입금 확인 알림을 보냄
class EstimateNotificationScheduler(APIView):
    RPA_D_SERVER_URL = f"{DEV4_SERVER}/user/notification"  # RPA-D 서버 URL

    @staticmethod
    def send_user_notification(user, departure_date, return_date):
        """
        사용자에게 계약금 입금 요청 알림을 보냅니다.
        """
        try:
            # 날짜 포맷팅 (일까지만 표시)
            formatted_departure_date = departure_date.strftime('%Y-%m-%d') if departure_date else "미정"
            formatted_return_date = return_date.strftime('%Y-%m-%d') if return_date else "미정"

            # 알림 제목과 내용 설정
            title = "계약금 입금 요청"
            body = f"출발일 : {formatted_departure_date} -> 도착일 : {formatted_return_date}의 견적의 계약금을 입금해주세요."

            # `send_notification` 함수로 알림 전송
            send_notification(user, title, body)

            print(f"[USER NOTIFICATION] Successfully sent notification to user {user.username}")
        except FCMToken.DoesNotExist:
            print(f"[USER NOTIFICATION] No FCM token found for user {user.username}")
        except Exception as e:
            print(f"[USER NOTIFICATION] Error sending notification to user {user.username}: {e}")


    @staticmethod
    def send_admin_notification(estimate_id):
        # 관리자에게 알림 전송
        notification_data = {
            "title": "계약금 입금 확인 요청",
            "content": f"견적 {estimate_id}의 계약금 입금을 확인해주세요.",
            "category": "일정",
            "send_datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        try:
            response = requests.post(EstimateNotificationScheduler.RPA_D_SERVER_URL, json=notification_data)
            if response.status_code == 201:
                print(f"Admin notification sent for estimate {estimate_id}")
            else:
                print(f"Failed to send admin notification: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error sending admin notification: {str(e)}")

    @staticmethod
    def send_notifications_for_pending_estimates():
        # 계약금 입금 대기 상태인 견적 찾기
        estimates = Estimate.objects.filter(status="계약금 입금 대기")
        for estimate in estimates:
            EstimateNotificationScheduler.send_user_notification(estimate.user, estimate.departure_date ,estimate.return_date)
            EstimateNotificationScheduler.send_admin_notification(estimate.id)

    @staticmethod
    def schedule_jobs():
        # 스케줄러 생성
        scheduler = BackgroundScheduler()
        # 매일 10시 실행
        scheduler.add_job(EstimateNotificationScheduler.send_notifications_for_pending_estimates, 'cron', hour=10, minute=0)
        # 매일 14시 실행
        scheduler.add_job(EstimateNotificationScheduler.send_notifications_for_pending_estimates, 'cron', hour=14, minute=0)
        scheduler.start()

    # 수동 실행용 API 추가
    def post(self, request):
        try:
            # 수동으로 알림 전송 작업 실행
            self.send_notifications_for_pending_estimates()
            return Response({
                "result": "true",
                "message": "알림 작업이 수동으로 실행되었습니다."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "result": "false",
                "message": f"오류 발생: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 서버 시작 시 스케줄러 실행
EstimateNotificationScheduler.schedule_jobs()


# TRP에서 받은 예약확정 상태를 저장하고 유저에게 알림
class EstimateStatusUpdateView(APIView):
    permission_classes = [AllowAny]
    ALLOWED_IPS = ALLOWED_HOSTS  # 허용할 IP 목록

    def patch(self, request) :
        client_ip = self.get_client_ip(request)
        if client_ip not in self.ALLOWED_IPS:
            return HttpResponseForbidden("Access denied: Unauthorized IP")
        
        # 요청 Body에서 estimate_id와 status 가져오기
        estimate_id = request.data.get("estimate_id")
        estimate_status = request.data.get("status")

        if not estimate_id:
            return Response({
                "result": "false",
                "message": "estimate_id가 요청에 포함되지 않았습니다."
            }, status=status.HTTP_400_BAD_REQUEST)

        if not estimate_status:
            return Response({
                "result": "false",
                "message": "status가 요청에 포함되지 않았습니다."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Estimate 객체 가져오기
            estimate = Estimate.objects.get(id=estimate_id)

            # 상태 업데이트
            estimate.status = estimate_status
            estimate.save()

            # 유저 알림 전송
            if estimate.status == "예약 완료":
                self.notify_user(estimate)

            return Response({
                "result": "true",
                "message": "견적 상태가 변경되어 예약이 완료되었습니다",
                "data": {
                    "estimate_id": estimate.id,
                    "status": estimate.status
                }
            }, status=status.HTTP_200_OK)

        except Estimate.DoesNotExist:
            return Response({
                "result": "false",
                "message": "해당 견적을 찾을 수 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)

    def notify_user(self, estimate):
        # 날짜 포맷팅 (일까지만 표시)
        formatted_departure_date = estimate.departure_date.strftime('%Y-%m-%d') if estimate.departure_date else "미정"
        formatted_return_date = estimate.return_date.strftime('%Y-%m-%d') if estimate.return_date else "미정"
        
        """
        유저에게 상태 변경 알림 전송
        """
        title = "예약 완료 알림"
        body = f"출발일 : {formatted_departure_date} > 도착일 : {formatted_return_date}이 예약 완료 되었습니다."

        try:
            send_notification(estimate.user, title, body)

        except Exception as e:
            return Response({
                "result": "false",
                "message": "알림 전송 실패"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
 