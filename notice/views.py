from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Notice
from .serializers import NoticeSerializer
from config.pagination import Pagination

from django.db.models import ObjectDoesNotExist

class NoticeList(APIView):

    # 공지사항 조회
    def get(self, request):
        try:
            queryset = Notice.objects.all().order_by('-created_at')
            paginator = Pagination()
            page = paginator.paginate_queryset(queryset, request)

            if page is not None:
                serializer = NoticeSerializer(page, many=True)
                return Response({
                    "result": "true",
                    "message": "공지사항 조회 성공",
                    "data": {
                        "count": paginator.page.paginator.count,
                        "next": paginator.get_next_link(),
                        "previous": paginator.get_previous_link(),
                        "notices": serializer.data,
                    },
                }, status=status.HTTP_200_OK)

            serializer = NoticeSerializer(queryset, many=True)
            return Response({
                "result": "true",
                "message": "공지사항 조회 성공",
                "data": {
                    "count": len(serializer.data),
                    "next": None,
                    "previous": None,
                    "notices": serializer.data,
                },
            }, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({
                "result": "false",
                "message": "공지사항이 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "result": "false",
                "message": f"오류가 발생했습니다: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    # 공지사항 저장
    def post(self, request):
        try:
            serializer = NoticeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "result": "true",
                    "message": "공지사항 저장 성공",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "result": "false",
                "message": "입력 데이터가 유효하지 않습니다.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "result": "false",
                "message": f"오류가 발생했습니다: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




    
