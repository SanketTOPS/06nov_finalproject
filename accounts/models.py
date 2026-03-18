from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    fullname = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    
    def __str__(self):
        return self.username
