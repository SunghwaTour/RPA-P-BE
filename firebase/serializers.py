from rest_framework import serializers
from .models import FCMToken

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ['token']

    def create(self, validated_data):
        user = self.context['request'].user  # 요청을 보낸 사용자
        token = validated_data['token']

        # 기존에 등록된 토큰이 있다면 업데이트, 없으면 새로 생성
        fcm_token, created = FCMToken.objects.update_or_create(
            user=user,
            defaults={'token': token}
        )
        return fcm_token
