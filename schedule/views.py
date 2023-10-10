from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm, ProfileForm
from .models import CustomUser, Profile
from django.shortcuts import redirect
from django.http import JsonResponse


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

        Profile.objects.create(user=user, username=username,
                                       content='これはデフォルトのプロフィールです。好みに応じて編集してください')

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
  profile = Profile.objects.get(user_id=user_id)
  hobbies = profile.hobby.all()
  interests = profile.interest.all()
  follows = profile.follows.all()
  followers = profile.followed_by.all()
  context = {
    'profile': profile,
    'hobbies': hobbies,
    'interests': interests,
    'follows': follows,
    'followers': followers,
  }
  return render(request, 'profile.html', context)

def profile_edit(request):
  ages = list(range(18, 51))
  if request.method == 'POST':
    profile = Profile.objects.filter(user=request.user).first()
    form = ProfileForm(request.POST, request.FILES)
    if form.is_valid():
      profile_data = form.cleaned_data
      if profile:

        fields = ['username', 'image', 'residence', 'age', 'gender', 'content']
        for field in fields:
          if profile_data.get(field):
            setattr(profile, field, profile_data[field])

        hobbies = profile_data.get('hobby', [])
        interests = profile_data.get('interest', [])
        if hobbies:
            profile.hobby.set(hobbies)
        if interests:
            profile.interest.set(interests)

        profile.save()

      else:
        profile = form.save(commit=False)
        profile.user = request.user
        profile.save()
        form.save_m2m()

      return redirect('profile', user_id=request.user.id)
  else:
    form = ProfileForm()
  context = {
        'form': form,
        'ages': ages,
      }
  return render(request, 'profile_edit.html', context)

def follow(request, user_id):
    try:
        user_to_toggle = CustomUser.objects.get(id=user_id)
        is_following = False
        if request.user.profile.follows.filter(id=user_to_toggle.profile.id).exists():
            request.user.profile.follows.remove(user_to_toggle.profile)
        else:
            request.user.profile.follows.add(user_to_toggle.profile)
            is_following = True

        response_data = {
            'success': True,
            'is_following': is_following
        }
    except CustomUser.DoesNotExist:
        pass

    return JsonResponse(response_data)

def get_follow_status(request, user_id):
    user_to_toggle = CustomUser.objects.get(id=user_id)
    follow_status = request.user.profile.follows.filter(id=user_to_toggle.profile.id).exists()
    return JsonResponse({'success': follow_status})
