from django.apps import AppConfig
from .firebase import initialize_firebase


class FirebaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'firebase'
    
    def ready(self):
        initialize_firebase()  # Firebase 초기화
