from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import FCMTokenSerializer
from rest_framework import status

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