from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime

class CustomUser(AbstractUser):
  is_guest = models.BooleanField(default=False)

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
    image = models.ImageField(
        upload_to='item_images/',
        default=os.getenv('CLOUDINARY_DEFAULT_IMAGE_URL','item_images/フリー女.jpeg'),
        null=True,
        blank=True
    )
    age = models.IntegerField(null=True, blank=True, default=0)
    gender = models.CharField(max_length=50)
    residence = models.CharField(max_length=255, default='〇〇県')
    content = models.TextField(max_length=255)
    hobby = models.ManyToManyField(Hobby)
    interest = models.ManyToManyField(Interest)
    follows = models.ManyToManyField('self', related_name='followed_by', symmetrical=False)

class Calendar(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    selectedDate = models.DateField(default='2023-01-14')
    free = models.CharField(max_length=20)
    time = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField(max_length=255, null=True, blank=True)

class UserRequest(models.Model):
    sender = models.ForeignKey(CustomUser, related_name="sent_request", on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name="received_request", on_delete=models.CASCADE)
    eventId = models.ForeignKey('Event', on_delete=models.CASCADE, null=True)
    userData = models.DateField(default='2023-01-14', null=True)
    is_processed = models.BooleanField(default=False)
    situation = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class UserResponse(models.Model):
    sender = models.ForeignKey(CustomUser, related_name="sent_response", on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name="received_response", on_delete=models.CASCADE)
    eventId = models.ForeignKey('Event', on_delete=models.CASCADE, null=True)
    userData = models.DateField(default='2023-01-14', null=True)
    buttonType = models.CharField(max_length=100)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    sender = models.ForeignKey(CustomUser, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField()
    room_name = models.CharField(max_length=30)
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

class Event(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)
    title = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    date = models.DateField()
    time = models.CharField(max_length=20)
    category = models.CharField(max_length=30)
    detail = models.TextField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
