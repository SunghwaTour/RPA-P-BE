from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.conf import settings

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username must be set')

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user 

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, **extra_fields)

# User
class User(AbstractBaseUser, PermissionsMixin):
    is_anonymous = False
    is_authenticated = True
    is_active = True

    username = models.CharField(max_length=255, unique=True)  # 사용자 이름 (중복 불가)
    phone_number = models.CharField(max_length=15, unique=True)  # 전화번호 (중복 불가) 
    
    is_active = models.BooleanField(default=True)  # 사용자 활성화 여부
    is_staff = models.BooleanField(default=False)  # 관리자 여부
    
    is_superuser = models.BooleanField(default=False)  # 관리자 여부 추가
    last_login = models.DateTimeField(null=True, blank=True)  # 마지막 로그인 시간 필드 추가


    USERNAME_FIELD = 'username'  # 로그인에 사용할 필드 지정
    REQUIRED_FIELDS = []  # 추가로 필요한 필드가 있다면 이 리스트에 추가

    objects = UserManager()

    def __str__(self):
        return self.username

class Notification(models.Model):
    CATEGORY_CHOICES = (
        ("공지사항", "공지사항"),
        ("견적", "견적"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    title = models.CharField(max_length=255)  # 알림 제목
    content = models.TextField()  # 알림 내용
    is_read = models.BooleanField(default=False)  # 읽음 여부
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)  # 카테고리
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간
