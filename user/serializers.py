from datetime import datetime
from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache

class SignUpSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True) # 전화번호 확인 필드

    class Meta:
        model = User
        fields = ['user_id', 'username', 'password', 'password_confirm', 'phone_number', 'last_login']
        extra_kwargs = {'password': {'write_only': True}} # 비밀번호는 쓰기 전용

    
    def validate(self, data):
        # 비밀번호 일치 확인
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password" : "비밀번호가 일치하지 않습니다."})
        
        # 전화번호 인증 확인 (캐시에서 인증 코드가 있는지 확인)
        phone_number = data.get('phone_number')

        if not cache.get(f"verified_{phone_number}"):
            raise serializers.ValidationError({"phone_number": "전화번호 인증이 완료되지 않았습니다."})

        return data

    # User 생성
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create(
            username=validated_data['username'],
            phone_number=validated_data['phone_number'],
            last_login=datetime.now(),
        )
        user.password = make_password(validated_data['password'])
        
        user.save()
        return user
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError("사용자명과 비밀번호는 필수 항목입니다.")
        
        # 사용자 이름으로 유저를 찾고, 비밀번호를 검증
        try:
            user = User.objects.get(username=username)
            if not user.check_password(password):  # 비밀번호 검증
                raise serializers.ValidationError("잘못된 비밀번호입니다.")
        except User.DoesNotExist:
            raise serializers.ValidationError("해당 사용자 이름을 찾을 수 없습니다.")

        # 검증에 성공하면 유저 객체를 반환
        data['user'] = user
        return data