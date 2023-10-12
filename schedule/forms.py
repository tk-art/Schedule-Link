from django import forms
from django.core.exceptions import ValidationError
from .models import CustomUser, Hobby, Interest, Profile, Calendar

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
    username = forms.CharField(required=False)
    residence = forms.CharField(required=False)
    age = forms.IntegerField(required=False)
    gender = forms.CharField(required=False)
    content = forms.CharField(required=False)
    image = forms.ImageField(required=False)

    hobby = forms.ModelMultipleChoiceField(
        queryset=Hobby.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    interest = forms.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Profile
        fields = ['username', 'residence', 'image', 'content', 'age', 'gender', 'hobby', 'interest']

class CalendarForm(forms.ModelForm):
    time = forms.CharField(required=False)
    message = forms.CharField(required=False)

    class Meta:
        model = Calendar
        fields = ['free', 'time', 'message']