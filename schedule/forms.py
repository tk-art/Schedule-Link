from django import forms
from django.core.exceptions import ValidationError
from .models import CustomUser, Hobby, Interest, Profile

class SignupForm(forms.ModelForm):
    email_conf = forms.EmailField()
    password_conf = forms.CharField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        email_confirmation = cleaned_data.get('email_conf')
        password = cleaned_data.get('password')
        password_confirmation = cleaned_data.get('password_conf')

        if email != email_confirmation:
            raise ValidationError('メールアドレスが一致しません')

        if password != password_confirmation:
            raise ValidationError('パスワードが一致しません')

        return cleaned_data


class ProfileForm(forms.ModelForm):
    hobby = forms.ModelMultipleChoiceField(
        queryset=Hobby.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )
    interest = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Profile
        fields = ['username', 'residence', 'image', 'content', 'age', 'gender', 'hobby', 'interest']