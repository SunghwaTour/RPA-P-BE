from twilio.rest import Client
from django.conf import settings
import random

# Twilio 클라이언트 설정
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

# 인증 코드 생성
def generate_verification_code():
    return random.randint(1000, 9999)  # 4자리 랜덤 숫자 생성

# 인증 코드 전송 함수
def send_verification_code(phone_number, code):
    message = client.messages.create(
        body=f"인증 코드는 {code} 입니다.",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=f'+82{phone_number[1:]}'
    )
    return message.sid