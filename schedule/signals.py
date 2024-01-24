from allauth.account.signals import user_signed_up, user_logged_in
from django.dispatch import receiver
from .models import Profile
from django.shortcuts import redirect

@receiver(user_signed_up)
def google_create_user(request, user, **kwargs):
    Profile.objects.create(
        user=user, username=user.first_name, content='これはデフォルトのプロフィールです。好みに応じて編集してください'
    )

@receiver(user_logged_in)
def social_login_redirect(request, user, **kwargs):
    custom_redirect_url = f'/profile/{user.id}/'
    request.session['custom_redirect_url'] = custom_redirect_url
