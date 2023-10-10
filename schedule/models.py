from django.db import models

from django.contrib.auth.models import AbstractUser
from datetime import datetime

class CustomUser(AbstractUser):
  pass

class Hobby(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Interest(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)
    age = models.IntegerField(null=True, blank=True, default=0)
    gender = models.CharField(max_length=50)
    residence = models.CharField(max_length=255, default='〇〇県')
    content = models.TextField(max_length=255)
    hobby = models.ManyToManyField(Hobby)
    interest = models.ManyToManyField(Interest)
    follows = models.ManyToManyField('self', related_name='followed_by', symmetrical=False)
