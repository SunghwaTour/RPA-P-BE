from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")  # 시간 포맷 변경

    class Meta:
        model = Notification
        fields = ["id", "title", "content", "is_read", "category", "created_at"]
