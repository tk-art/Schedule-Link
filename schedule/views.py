from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm
from .models import CustomUser
from django.shortcuts import redirect

def top(request):
  return render(request, 'top.html')

def signup(request):
  if request.method == 'POST':
    form = SignupForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        email = form.cleaned_data.get('email')
        hash_password = make_password(form.cleaned_data.get('password'))

        user = CustomUser.objects.create(username=username, email=email, password=hash_password)

        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return redirect('top')

  else:
    form = SignupForm()
  return render(request, 'signup.html', {'form': form})

def login_view(request):
  error_message = ""
  if request.method == 'POST':
    username = request.POST.get('username')
    password = request.POST.get('password')

    user = authenticate(request, username=username, password=password)
    if user:
      user.backend = 'django.contrib.auth.backends.ModelBackend'
      login(request, user)
      return redirect('top')
    else:
      error_message = 'ユーザーネームかパスワードが違います、もう一度お試しください'
  return render(request, 'login.html', {'error_message': error_message})

def logout_view(request):
  logout(request)
  return redirect('top')

def profile(request, user_id):
  return render(request, 'profile.html')
