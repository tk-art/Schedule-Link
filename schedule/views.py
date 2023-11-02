from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm, ProfileForm, CalendarForm
from .models import CustomUser, Profile, Calendar, UserRequest, UserResponse
from django.shortcuts import redirect
from django.http import JsonResponse
from django.core.serializers import serialize
from django.contrib import messages
from datetime import datetime

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
  calendars = Calendar.objects.filter(user=profile.user)

  current_user = request.user == profile.user

  context = {
    'profile': profile,
    'hobbies': hobbies,
    'interests': interests,
    'follows': follows,
    'followers': followers,
    'current_user': current_user
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

def calendar(request):
  if request.method == 'POST':
    form = CalendarForm(request.POST)
    if form.is_valid():
      selected_date = form.cleaned_data.get('selectedDate')
      calendar_entry = Calendar.objects.filter(user=request.user, selectedDate=selected_date).first()

      if calendar_entry:
        for field in form.changed_data:
          setattr(calendar_entry, field, form.cleaned_data[field])
        calendar_entry.save()

      else:
        form.instance.user = request.user
        form.save()
      return redirect('profile', user_id=request.user.id)
  else:
      form = CalendarForm()
  return render(request, 'profile.html', {'form': form})


def get_calendar_events(request, user_id):
    events = Calendar.objects.filter(user=user_id)
    json_data = [{
      'title': event.free,
      'start': event.selectedDate,
    } for event in events]
    return JsonResponse(json_data, safe=False)

def get_event_data(request, user_id):
    selected_date = request.GET.get('date')
    event = Calendar.objects.filter(user_id=user_id, selectedDate=selected_date).first()

    if not event:
        return JsonResponse({}, status=404)

    data = {
        'title': event.free,
        'time': event.time,
        'message': event.message,
    }

    return JsonResponse(data)

def delete_calendar(request):
  if request.method == 'POST':
    user_id = request.POST.get('user_id')
    delete_date = request.POST.get('deleteDate')

    calendar_entry = Calendar.objects.get(user_id=user_id, selectedDate=delete_date)
    calendar_entry.delete()
    return redirect('profile', user_id=user_id)

def intentional_request(request, user_id):
    if request.method == "POST":
        sender = request.user
        receiver = CustomUser.objects.get(id=user_id)
        userData = request.POST.get('userData')

        UserRequest.objects.create(sender=sender, receiver=receiver, userData=userData)

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"})

def request_list(request):
    current_user = request.user
    request_users = UserRequest.objects.filter(receiver_id=current_user.id).order_by('-created_at')
    response_users = UserResponse.objects.filter(receiver_id=current_user.id).order_by('-created_at')
    users = automatic_request_list(request)

    context = {
      'request_users': request_users,
      'response_users': response_users,
      'users': users,
      'current_user': current_user
    }
    return render(request, 'request_list.html', context)



def automatic_request_list(request):
    current_user = request.user
    today_date = datetime.now().date()

    user_free_times = Calendar.objects.filter(user=current_user, selectedDate__gte=today_date)
    user_profile = Profile.objects.get(id=current_user.profile.id)
    range_profile = Profile.objects.filter(residence="宮崎県")

    followed_users = current_user.profile.follows.all()

    all_matched_users = []

    for user_free_time in user_free_times:
        matched_users = Calendar.objects.filter(
            selectedDate=user_free_time.selectedDate
        ).exclude(user=current_user).values_list('user', flat=True)
        all_matched_users.extend(matched_users)

    followed_user_ids = [profile.user.id for profile in current_user.profile.follows.all()]

    priority_matching = []
    regular_matching = []

    for profile in range_profile:
        if profile.id == user_profile.id:
           continue

        if profile.user_id in followed_user_ids:
            priority_matching.append(profile.user_id)
            continue

        if set(profile.hobby.all()).intersection(set(user_profile.hobby.all())):
            regular_matching.append(profile.user_id)
            continue

        if set(profile.interest.all()).intersection(set(user_profile.interest.all())):
            regular_matching.append(profile.user_id)

    matching_users = priority_matching + regular_matching

    semifinal_matched_users = list(set(all_matched_users) & set(matching_users))

    additional_users = [user for user in all_matched_users if user not in semifinal_matched_users]

    final_matched_users = semifinal_matched_users + additional_users

    users = sorted(CustomUser.objects.filter(id__in=final_matched_users), key=lambda u: final_matched_users.index(u.id))
    return users




def process_button(request, user_id):
    if request.method == 'POST':
      buttonType = request.POST.get('buttonType')
      sender = request.user
      receiver = CustomUser.objects.get(id=user_id)
      userData = request.POST.get('userData')

      UserResponse.objects.create(sender=sender, receiver=receiver, userData=userData, buttonType=buttonType)

      user_request = UserRequest.objects.get(receiver=sender)
      user_request.is_processed = True
      user_request.save()

      messages.success(request, '正常にレスポンスが送信されました')
      return redirect('request_list')

      messages.error(request, 'エラーが発生しました')
    return render(request, 'request_list.html')