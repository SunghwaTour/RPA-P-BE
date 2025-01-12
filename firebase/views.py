from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import FCMTokenSerializer
from rest_framework import status
from .send_message import send_notification
# FCM 토큰 등록 API
class FCMTokenRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({
                "result": "true",
                "message": "FCM 토큰이 성공적으로 저장되었습니다."
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "result": "false",
            "message": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

# 알림 테스트 API
class TestNotificationView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def post(self, request):
        user = request.user
        send_notification(user, "테스트 알림", "이것은 테스트 알림입니다.")
        return Response({"message": "Notification sent!"})