from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Member(models.Model):
    name = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10)
    province = models.CharField(max_length=100, null=True, blank=True)
    motto = models.TextField(default='', null=True, blank=True)

    def __str__(self):
        return self.name.username
