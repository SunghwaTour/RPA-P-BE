from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import FCMTokenSerializer
from rest_framework import status
from .models import FCMToken
from .send_message import send_fcm_notification

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

class SendNotificationView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")  # 사용자 ID
        title = request.data.get("title")      # 알림 제목
        body = request.data.get("body")        # 알림 내용

        # 사용자 FCM 토큰 가져오기
        try:
            fcm_token = FCMToken.objects.get(user_id=user_id).token
        except FCMToken.DoesNotExist:
            return Response({"error": "FCM Token not found for the user."}, status=status.HTTP_404_NOT_FOUND)

        # 알림 전송
        if send_fcm_notification(fcm_token, title, body):
            return Response({"message": "Notification sent successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Failed to send notification."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
