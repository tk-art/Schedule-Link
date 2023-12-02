from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm, ProfileForm, CalendarForm, SearchForm
from .models import CustomUser, Profile, Calendar, UserRequest, UserResponse, ChatMessage
from django.shortcuts import redirect
from django.http import JsonResponse
from django.core.serializers import serialize
from django.contrib import messages
import pytz
from datetime import datetime
from django.db import models
from django.db.models import Q

def human_readable_time_from_utc(timestamp, timezone='Asia/Tokyo'):
    local_tz = pytz.timezone(timezone)
    local_now = datetime.now(local_tz)
    local_timestamp = timestamp.astimezone(local_tz)
    delta = local_now - local_timestamp

    seconds = int(delta.total_seconds())
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    if days > 0:
        return f"{days}日前"
    elif hours > 0:
        return f"{hours}時間前"
    elif minutes > 0:
        return f"{minutes}分前"
    else:
        return "たった今"

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

        hobbies = profile_data.get('hobby')
        interests = profile_data.get('interest')
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

        UserRequest.objects.create(sender=sender, receiver=receiver, userData=userData, situation=True)

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"})

def check_user_request(request, user_id):
    userData = request.POST.get('userData')
    user_request = UserRequest.objects.filter(
        sender=request.user.id,
        receiver_id=user_id,
        userData=userData
    ).order_by('-created_at').first()

    if user_request and user_request.situation:
        return JsonResponse({'situation': True})
    else:
        return JsonResponse({'situation': False})

def request_list(request):
    current_user = request.user
    request_users = UserRequest.objects.filter(receiver_id=current_user.id).order_by('-created_at')
    response_users = UserResponse.objects.filter(receiver_id=current_user.id).order_by('-created_at')
    users, user_first_match = automatic_request_list(request)

    context = {
      'request_users': request_users,
      'response_users': response_users,
      'users': users,
      'current_user': current_user,
      'user_first_match': user_first_match
    }
    return render(request, 'request_list.html', context)

def automatic_request_list(request):
    current_user = request.user
    today_date = datetime.now().date()

    user_free_times = Calendar.objects.filter(user=current_user, selectedDate__gte=today_date)
    user_profile = Profile.objects.get(id=current_user.profile.id)
    range_profile = Profile.objects.filter(residence="宮崎県")

    followed_users = current_user.profile.follows.all()

    user_first_match = {}

    for user_free_time in user_free_times:
        matched_users = Calendar.objects.filter(
            selectedDate=user_free_time.selectedDate
        ).exclude(user=current_user)

        for matched_user in matched_users:
            user_id = matched_user.user.id
            if user_id not in user_first_match:
                user_first_match[user_id] = matched_user.selectedDate

    first_matched_users = list(user_first_match.keys())

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

    semifinal_matched_users = list(set(first_matched_users) & set(matching_users))

    additional_users = [user for user in first_matched_users if user not in semifinal_matched_users]

    final_matched_users = semifinal_matched_users + additional_users

    users = sorted(CustomUser.objects.filter(id__in=final_matched_users), key=lambda u: final_matched_users.index(u.id))
    return users, user_first_match

def process_button(request, user_id):
    if request.method == 'POST':
      buttonType = request.POST.get('buttonType')
      sender = request.user
      receiver = CustomUser.objects.get(id=user_id)
      userData = request.POST.get('userData')

      UserResponse.objects.create(sender=sender, receiver=receiver, userData=userData, buttonType=buttonType)

      user_request = UserRequest.objects.get(sender=receiver, receiver=sender, userData=userData)
      user_request.is_processed = True
      user_request.save()

      messages.success(request, '正常にレスポンスが送信されました')
      return redirect('request_list')

      messages.error(request, 'エラーが発生しました')
    return render(request, 'request_list.html')

def check_new_requests(request):
    user = request.user
    requests_unread = UserRequest.objects.filter(receiver=user, read=False).exists()
    responses_unread = UserResponse.objects.filter(receiver=user, read=False).exists()

    response = {
      'requests_unread': requests_unread,
      'responses_unread': responses_unread
    }
    return JsonResponse(response)

def mark_tab_as_read(request):
    user = request.user
    request_type = request.POST.get('type')

    if request_type == 'request':
        queryset = UserRequest.objects.filter(receiver=user, read=False)
    elif request_type == 'response':
        queryset = UserResponse.objects.filter(receiver=user, read=False)
    else:
        return JsonResponse({'status': 'error', 'message': '無効なリクエストタイプ'})

    queryset.update(read=True)

    return JsonResponse({'status': 'success'})

def chat_list(request):
    current_user = request.user
    user_rooms = ChatMessage.objects.filter(
        models.Q(sender=current_user) | models.Q(receiver=current_user)
    ).values_list('room_name', flat=True).distinct()

    rooms_receiver= []

    for room_name in user_rooms:
        room_info = {}
        last_room = ChatMessage.objects.filter(room_name=room_name).last()
        last_room.delta = human_readable_time_from_utc(last_room.timestamp)
        room_info['message'] = last_room.message
        room_info['delta'] = last_room.delta
        room_info['timestamp'] = last_room.timestamp
        if last_room.sender == current_user:
            room_info['receiver'] = last_room.receiver
        else:
            room_info['receiver'] = last_room.sender
        rooms_receiver.append(room_info)

    rooms_receiver_sorted = sorted(rooms_receiver, key=lambda x: x['timestamp'], reverse=True)
    return render(request, 'chat_list.html', {'rooms': rooms_receiver_sorted})


def chat_room(request, user_id):
    other_user = CustomUser.objects.get(id=user_id)
    current_user = request.user
    room_name = f'{min(current_user.id, other_user.id)}_{max(current_user.id, other_user.id)}'
    chat_messages = ChatMessage.objects.filter(room_name=room_name)

    for chat in chat_messages:
      chat.delta = human_readable_time_from_utc(chat.timestamp)

    context = {
      'current_user': current_user,
      'other_user': other_user,
      'room_name': room_name,
      'chat_messages': chat_messages
    }

    return render(request, 'chat.html', context)

def check_unread_messages(request, user_id):
    current_user = request.user
    other_user = CustomUser.objects.get(id=user_id)
    chat_unread = ChatMessage.objects.filter(sender=other_user, receiver=current_user, read=False).exists()

    response = {
      'chat_unread': chat_unread
    }
    return JsonResponse(response)

def mark_chat_as_read(request, user_id):
    user = request.user
    other_user = CustomUser.objects.get(id=user_id)

    chat_room = ChatMessage.objects.filter(
      Q(sender=user, receiver=other_user) | Q(sender=other_user, receiver=user)
    ).first()
    room_name = chat_room.room_name
    ChatMessage.objects.filter(room_name=room_name, read=False).update(read=True)

    return JsonResponse({'status': 'success'})

def search(request):
    ages = list(range(18, 51))
    if request.method == 'POST':
      form = SearchForm(request.POST)
      if form.is_valid():
          residence = form.cleaned_data.get('residence')
          gender = form.cleaned_data.get('gender')
          min_age = form.cleaned_data.get('min_age')
          max_age = form.cleaned_data.get('max_age')

          hobby = form.cleaned_data.get('hobby')
          interest = form.cleaned_data.get('interest')

          my_profile = Profile.objects.get(user=request.user)

          profiles = Profile.objects.all().exclude(id=my_profile.id)
          if residence:
              profiles = profiles.filter(residence=residence)
          if min_age:
              profiles = profiles.filter(age__gte=min_age)
          if max_age:
              profiles = profiles.filter(age__lte=max_age)
          if gender:
              profiles = profiles.filter(gender=gender)
          if hobby:
              profiles = profiles.filter(hobby__in=hobby).distinct()
          if interest:
              profiles = profiles.filter(interest__in=interest).distinct()



          context = {
            'profiles': profiles
          }

          if profiles:
              return render(request, 'search_results.html', context)
          else:
              not_profiles = "現在検索された内容に合致するユーザーが見つかりませんでした。"
              return render(request, 'search.html', {'not_profiles': not_profiles})
    else:
      form = SearchForm()

    context = {
      'ages':ages,
      'form': form
    }
    return render(request, 'search.html', context)
