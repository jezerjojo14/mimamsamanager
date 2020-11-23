from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    displayName=models.CharField(max_length=50)
    inactive=models.BooleanField(default=False)

class Post(models.Model):
    title = models.CharField(max_length=200)
    content=models.TextField()
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    time=models.DateTimeField(default=timezone.now)
    edited=models.BooleanField(default=False)
