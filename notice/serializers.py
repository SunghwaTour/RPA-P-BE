from rest_framework import serializers
from .models import Notice
from datetime import datetime

class NoticeSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()  # 날짜 변환

    class Meta:
        model = Notice
        fields = ['id', 'type', 'title', 'date', 'detail']

    def get_date(self, obj):
        # created_at 값을 "yyyy-MM-dd HH:mm" 형식으로 변환
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    

