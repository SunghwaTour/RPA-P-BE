import os
from firebase_admin import credentials, initialize_app, get_app, delete_app
from config.settings import BASE_DIR

#  Firebase 초기화 함수. 이미 초기화된 경우 재초기화합니다.
def initialize_firebase():
    try:
        # 기존 앱이 초기화되어 있다면 재초기화
        app = get_app()
        delete_app(app)
    except ValueError:
        # 초기화되지 않은 경우 무시
        pass

    # Firebase Admin SDK 인증 JSON 파일 경로
    cred_path = os.path.join(BASE_DIR, 'firebase/sunghwatour-firebase-adminsdk.json')
    cred = credentials.Certificate(cred_path)
    initialize_app(cred)
