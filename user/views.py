from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from .serializers import SignUpSerializer, LoginSerializer
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.utils import timezone
from .twilio import generate_verification_code, send_verification_code
from .models import User
from django.core.cache import cache
from datetime import datetime

# 로그인 or 회원가입
class UserManagementView(APIView) :
    permission_classes = [AllowAny]

    def post(self, request):
        # 아이디, 전화번호 입력받음
        username = request.data.get('username')
        phone_number = request.data.get('phone_number')

        if not username or not phone_number:
            return Response({
                "result": "false",
                "message": "사용자명과 전화번호는 필수 항목입니다."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # DB에 사용자 존재하는지 확인
            user = User.objects.filter(username=username, phone_number=phone_number).first()

            # 이미 회원가입 했으면
            if user:
                # 로그인 처리 전에 전화번호 인증 확인
                if not cache.get(f"verified_{phone_number}"):
                    return Response({
                        "result": "false",
                        "message": "전화번호 인증이 완료되지 않았습니다."
                    }, status=status.HTTP_400_BAD_REQUEST)

                # JWT 토큰 생성
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                return Response({
                    "data": {
                        "refresh": refresh_token,
                        "access": access_token,
                        "username": user.username,
                    },
                    "message": "로그인 성공",
                }, status=status.HTTP_200_OK)

            # 처음 로그인할 때
            else:
                # 회원가입 처리
                if not cache.get(f"verified_{phone_number}"):
                    return Response({
                        "result": "false",
                        "message": "전화번호 인증이 완료되지 않았습니다."
                    }, status=status.HTTP_400_BAD_REQUEST)

                user = User.objects.create(
                    username=username,
                    phone_number=phone_number,
                    last_login=datetime.now(),
                )
                user.save()

                # JWT 토큰 생성
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                return Response({
                    "data": {
                        "refresh": refresh_token,
                        "access": access_token,
                        "username": user.username,
                    },
                    "message": "회원가입 성공 and 로그인 성공",
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "result": "false",
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 토큰 재발급
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]  

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)

        try:
            # 토큰 유효성 검사
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            # 토큰이 유효하지 않거나 만료된 경우
            return Response({
                'result': 'false',
                'data': None,
                'message': {'token': ['토큰이 유효하지 않거나 만료 됐습니다']}
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 유효한 경우, 새로운 access 토큰 반환
        response_data = serializer.validated_data
        return Response({
            'result': 'true',
            'data': response_data,
            'message': '토큰 재발급 성공'
        }, status=status.HTTP_200_OK)

# 전화번호 인증 전송
class SendCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            response = {
                'result': False,
                'message': '전화번호를 입력해주세요'
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        # 요청 카운트 및 타임스탬프 가져오기
        request_count = cache.get(f'request_count_{phone_number}', 0)
        first_request_time = cache.get(f'first_request_time_{phone_number}')

        current_time = timezone.now()

        # 요청이 1시간(3600초) 이내일 경우 요청 카운트 증가
        if first_request_time:
            time_diff = (current_time - first_request_time).total_seconds()
            if time_diff < 360:  # 10분 이내
                if request_count >= 5:  # 최대 요청 횟수 제한 (예: 5회)
                    response = {
                        'result': False,
                        'message': '인증 코드는 1시간마다 최대 5회 요청할 수 있습니다.'
                    }
                    return Response(response, status=status.HTTP_429_TOO_MANY_REQUESTS)
                else:
                    request_count += 1
            else:
                # 1시간 이상 지났으면 카운트 및 타임스탬프 리셋
                request_count = 1
                first_request_time = current_time
        else:
            # 처음 요청 시 타임스탬프 설정
            request_count = 1
            first_request_time = current_time

        # 현재 요청 시간 저장
        cache.set(f'first_request_time_{phone_number}', first_request_time, timeout=360)  # 타임스탬프 캐시에 저장 (10분 유지)
        cache.set(f'request_count_{phone_number}', request_count, timeout=360)  # 요청 카운트 캐시에 저장 (10분 유지)

        try:
            # 인증 코드 생성 및 전송
            verification_code = generate_verification_code()
            send_verification_code(phone_number, verification_code)

            # 인증 코드를 캐시에 저장 (5분 동안 유지)
            cache.set(phone_number, verification_code, timeout=300)

            response = {
                'result': True,
                'message': '인증 코드가 성공적으로 전송되었습니다.'
            }
            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            response = {
                'result': False,
                'message': str(e)
            }
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 전화번호 인증 확인
class VerifyCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        verification_code = request.data.get('verification_code')

        if not phone_number or not verification_code:
            return Response({
                'result': False,
                'message': '전화번호와 인증 코드를 모두 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 캐시에서 저장된 인증 코드 가져오기
        stored_code = cache.get(phone_number)

        if stored_code is None:
            return Response({
                'result': 'false',
                'message': '인증 코드가 만료되었거나 잘못된 전화번호입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if verification_code == stored_code:
            cache.set(f"verified_{phone_number}", True, timeout=3600)  # 인증 완료 상태 캐시에 저장

            # 인증 성공 처리
            return Response({
                'result': True,
                'message': '인증이 성공적으로 완료되었습니다.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'result': False,
                'message': '잘못된 인증 코드입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

