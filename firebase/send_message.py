from firebase_admin import messaging

def send_fcm_notification(token, title, body):
    """
    FCM 알림을 전송하는 함수
    :param token: FCM 디바이스 토큰
    :param title: 알림 제목
    :param body: 알림 내용
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,  # 알림 제목
            body=body,    # 알림 내용
        ),
        token=token,  # 수신 디바이스의 FCM 토큰
    )
    try:
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
        return True
    except Exception as e:
        print(f"Failed to send message: {e}")
        return False
