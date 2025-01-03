from django.db import models

class Notice(models.Model) :
    NOTICES_TYPES = [
        ('일반', '일반'),
        ('버전', '버전'),
    ]
    type = models.CharField(max_length=10, choices=NOTICES_TYPES) # 공지 유형
    title = models.CharField(max_length=255) # 제목
    detail = models.TextField() # 내용
    created_at = models.DateTimeField(auto_now_add=True) # 만든 시간
    updated_at = models.DateTimeField(auto_now=True) # 수정된 시간
