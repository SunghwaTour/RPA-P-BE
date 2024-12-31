from django.db import models
from user.models import User
class FCMToken(models.Model) :
    user = models.ForeignKey(User, verbose_name=("fcm_tokens"), on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
