from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source="created_at", format="%Y-%m-%d %H:%M:%S")  # 날짜 포맷 변경

    class Meta:
        model = Notification
        fields = ["id", "title", "content", "is_read", "category", "date"]
