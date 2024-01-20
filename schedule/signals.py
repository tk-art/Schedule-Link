from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from .models import Profile

@receiver(user_signed_up)
def google_create_user(request, user, **kwargs):
    Profile.objects.create(
        user=user, username=user.first_name, content='これはデフォルトのプロフィールです。好みに応じて編集してください'
    )