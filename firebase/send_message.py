from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError
from .models import FCMToken

def send_notification(user, title, body):
    try:
        # 사용자에 대한 FCM 토큰 가져오기
        fcm_token = FCMToken.objects.get(user=user).token

        # 알림 메시지 구성
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=fcm_token,  # 클라이언트의 FCM 토큰
        )

        # Firebase로 알림 전송
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")

    except FCMToken.DoesNotExist:
        print(f"No FCM token found for user {user}")
    except FirebaseError as fe:
        print(f"Firebase error occurred: {fe}")
    except Exception as e:
        print(f"Error sending notification: {e}")

