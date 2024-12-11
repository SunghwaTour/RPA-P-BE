from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from .serializers import SignUpSerializer, LoginSerializer
from rest_framework.permissions import AllowAny
# 회원가입
class RegisterView(APIView):
    permission_classes = [AllowAny] 
    
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            # 전화번호 인증이 완료된 사용자만 회원가입 완료
            user = serializer.save()
            response = {
                'result': 'true',
                'user_id': user.user_id,
                'message': '회원가입이 완료되었습니다.'
            }
            return Response(response, status=status.HTTP_201_CREATED)
        
        data = 1 if 'non_field_errors' in serializer.errors else 2
        sta = status.HTTP_200_OK if 'non_field_errors' in serializer.errors else status.HTTP_400_BAD_REQUEST
        response = {
            'result': 'false',
            'data': data,
            'message': serializer.errors,
        }
        return Response(response, status=sta)


# 로그인
class LoginView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            # 사용자 인증
            user = serializer.validated_data['user']
            if user is not None:
                # JWT 토큰 생성
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                response_data = {
                    'refresh': refresh_token,
                    'access': access_token,
                    'user_id': user.user_id,
                    'username': user.username
                }
                return Response({
                    'result': 'true',
                    'data': response_data,
                    'message': '로그인 성공'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'result': 'false',
                    'message': '잘못된 사용자명 또는 비밀번호입니다.'
                }, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'result': 'false',
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


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
