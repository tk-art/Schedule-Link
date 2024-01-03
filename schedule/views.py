from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm, ProfileForm, CalendarForm, SearchForm, EventForm, EventEditForm
from .models import CustomUser, Profile, Calendar, UserRequest, UserResponse, ChatMessage, Notification, Event
from django.shortcuts import redirect
from django.http import JsonResponse
from django.core.serializers import serialize
from django.contrib import messages
import pytz
from datetime import datetime, date
from django.db import models
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.decorators import login_required

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
    category = request.GET.get('category', '')
    recommend_user = request.GET.get('recommend_user', '')
    recommend_event = request.GET.get('recommend_event', '')

    if recommend_user:
        users, user_first_match = recommendation_user_list(request)
    else:
        users = None
        user_first_match = None

    if recommend_event:
        matched_events = recommendation_event_list(request)
    else:
        matched_events = None

    if category:
        events = Event.objects.filter(category=category).order_by('-timestamp')
    else:
        events = Event.objects.all().order_by('-timestamp')

    for event in events:
        event.delta = human_readable_time_from_utc(event.timestamp)
        event.current_user = (request.user == event.user)

    context = {
        'events': events,
        'users': users,
        'user_first_match': user_first_match,
        'matched_events': matched_events
    }

    return render(request, 'top.html', context)

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
        return redirect('profile', user_id=request.user.id)

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
      request.session['last_follow_count'] = user.profile.followed_by.count()
      return redirect('profile', user_id=request.user.id)
    else:
      error_message = 'ユーザーネームかパスワードが違います、もう一度お試しください'
  return render(request, 'login.html', {'error_message': error_message})

def logout_view(request):
  logout(request)
  return redirect('top')

@login_required
def profile(request, user_id):
  profile = Profile.objects.get(user_id=user_id)

  hobbies = profile.hobby.all()
  interests = profile.interest.all()
  follows = profile.follows.all()
  followers = profile.followed_by.all()
  calendars = Calendar.objects.filter(user=profile.user)
  events = Event.objects.filter(user=profile.user).order_by('-timestamp')

  for event in events:
    event.delta = human_readable_time_from_utc(event.timestamp)

  current_user = request.user == profile.user

  context = {
    'profile': profile,
    'hobbies': hobbies,
    'interests': interests,
    'follows': follows,
    'followers': followers,
    'current_user': current_user,
    'events': events
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
    user = request.user
    user_to_toggle = CustomUser.objects.get(id=user_id)
    follow_status = request.user.profile.follows.filter(id=user_to_toggle.profile.id).exists()
    return JsonResponse({'success': follow_status})

def get_follower_count(request):
    last_follow_count = request.session.get('last_follow_count', 0)
    current_follow_count = request.user.profile.followed_by.count()

    if current_follow_count > last_follow_count:
      new_follower = True
    elif current_follow_count < last_follow_count:
      new_follower = False
      request.session['last_follow_count'] = current_follow_count
    else:
      new_follower = False

    return JsonResponse({'new_follower': new_follower})

def confirm_followers_viewed(request):
    current_follow_count = request.user.profile.followed_by.count()
    request.session['last_follow_count'] = current_follow_count
    return JsonResponse({'success': 'true'})


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
        eventId = request.POST.get('eventId')

        UserRequest.objects.create(sender=sender, receiver=receiver, userData=userData, eventId_id=eventId, situation=True)

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"})

def check_user_request(request, user_id):
    userData = request.POST.get('userData')
    eventId = request.POST.get('eventId')

    user_request = UserRequest.objects.filter(
        sender=request.user.id,
        receiver_id=user_id,
        userData=userData,
        eventId=eventId
    ).order_by('-created_at').first()

    if user_request and user_request.situation:
        return JsonResponse({'situation': True})
    else:
        return JsonResponse({'situation': False})

def request_list(request):
    current_user = request.user
    request_users = UserRequest.objects.filter(receiver_id=current_user.id).select_related('eventId').order_by('-created_at')
    response_users = UserResponse.objects.filter(receiver_id=current_user.id).select_related('eventId').order_by('-created_at')
    users, user_first_match = automatic_request_list(request)

    context = {
      'request_users': request_users,
      'response_users': response_users,
      'users': users,
      'current_user': current_user,
      'user_first_match': user_first_match
    }
    return render(request, 'request_list.html', context)

def get_matching_profiles(current_user):
    user_profile = Profile.objects.get(id=current_user.profile.id)
    range_profile = Profile.objects.filter(residence=user_profile.residence)

    followed_user_ids = [profile.user_id for profile in current_user.profile.follows.all()]

    priority_matching = []
    regular_matching = []

    for profile in range_profile:
        if profile.id == user_profile.id:
            continue

        if profile.user_id in followed_user_ids:
            priority_matching.append(profile.user_id)
        else:
            hobbies_in_common = set(profile.hobby.all()).intersection(set(user_profile.hobby.all()))
            interests_in_common = set(profile.interest.all()).intersection(set(user_profile.interest.all()))

            if hobbies_in_common or interests_in_common:
                regular_matching.append(profile.user_id)

    return priority_matching + regular_matching

def recommendation_user_list(request):
    current_user = request.user
    today_date = datetime.now().date()
    user_free_times = Calendar.objects.filter(user=current_user, selectedDate__gte=today_date)

    #mathing_users = 同じ県でフォローしているユーザ　＋　同じ県で趣味、興味に共通点があるユーザ
    matching_users = get_matching_profiles(current_user)

    #暇な時間が被っているユーザを取得
    user_first_match = {}
    for user_free_time in user_free_times:
        matched_users = Calendar.objects.filter(
            selectedDate=user_free_time.selectedDate
        ).exclude(user=current_user)

        for matched_user in matched_users:
            user_id = matched_user.user.id
            if user_id not in user_first_match:
                user_first_match[user_id] = matched_user.selectedDate

    #暇な時間がマッチしたユーザーのidだけをリスト化
    first_matched_users = list(user_first_match.keys())

    # = 暇な時間が一致しているユーザかつmathing_usersをリスト化
    final_matched_users = list(set(first_matched_users) & set(matching_users))

    #final_matched_users リストにリストされている順番と同じ順序でユーザーオブジェクトを並べ替え
    users = sorted(CustomUser.objects.filter(id__in=final_matched_users), key=lambda u: final_matched_users.index(u.id))
    return users, user_first_match

def recommendation_event_list(request):
    current_user = request.user
    today_date = datetime.now().date()
    user_free_times = Calendar.objects.filter(user=current_user, selectedDate__gte=today_date)

    #mathing_users = 同じ県でフォローしているユーザ　＋　同じ県で趣味、興味に共通点があるユーザ
    matching_users = get_matching_profiles(current_user)

    matched_events = []
    for user_free_time in user_free_times:
        temp_matched_events = Event.objects.filter(
            date=user_free_time.selectedDate
        ).exclude(user=current_user)

        # 一致するイベントをリストに追加
        for event in temp_matched_events:
            if event.user.id in matching_users:
                matched_events.append(event)

    for event in matched_events:
        event.delta = human_readable_time_from_utc(event.timestamp)

    return matched_events

def process_button(request, user_id):
    if request.method == 'POST':
      buttonType = request.POST.get('buttonType')
      sender = request.user
      receiver = CustomUser.objects.get(id=user_id)
      userData = request.POST.get('userData')
      event_id = int(request.POST.get('eventId'))
      eventId = Event.objects.get(id=event_id)

      UserResponse.objects.create(sender=sender, receiver=receiver, userData=userData, eventId=eventId, buttonType=buttonType)

      if eventId:
        user_request = UserRequest.objects.get(sender=receiver, receiver=sender, eventId=eventId)
      else:
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

@login_required
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


          today = date.today()
          for profile in profiles:
            calendar = Calendar.objects.filter(
              user_id=profile.user.id,
              selectedDate__gt=today).order_by('selectedDate').first()
            if calendar:
              profile.calendar = calendar.selectedDate
            else:
              profile.calendar = None

          sorted_profiles = sorted(profiles, key=lambda p: p.calendar or date.max)

          if profiles:
              return render(request, 'search_results.html', {'profiles' : sorted_profiles})
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

def event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data.get('title')
            image = form.cleaned_data.get('image')
            if image == None:
              image = 'item_images/フリー女.jpeg'
            detail = form.cleaned_data.get('detail')
            place = form.cleaned_data.get('place')
            datetime = form.cleaned_data.get('datetime')
            category = form.cleaned_data.get('category')

            date, time = datetime.split(' ')

            Event.objects.create(
                user=request.user, title=title, place=place, category=category, date=date,
                time=time, image=image, detail=detail
            )

            return redirect('profile', user_id=request.user.id)

    else:
      form = EventForm()
    return render(request, 'event.html', {'form': form})

def get_event_details(request):
    event_id = request.GET.get('event_id')
    event = Event.objects.get(id=event_id)

    event.delta = human_readable_time_from_utc(event.timestamp)

    event.current_user = (request.user == event.user)

    data = {
      'title': event.title,
      'place': event.place,
      'date': event.date,
      'time': event.time,
      'detail': event.detail,
      'image_url': event.image.url,
      'delta': event.delta,
      'profile_url': event.user.profile.image.url,
      'username': event.user.profile.username,
      'current_user': event.current_user
    }
    return JsonResponse(data)

# カード編集、削除

def card_editing(request, event_id):
    if request.method == 'POST':
        event = Event.objects.filter(id=event_id).first()
        form = EventEditForm(request.POST, request.FILES)
        if form.is_valid():
            event_data = form.cleaned_data
            if event:
                fields = ['image', 'title', 'place', 'datetime', 'category', 'detail']
                for field in fields:
                    if event_data.get(field):
                        if field == 'datetime':
                            date, time = event_data[field].split(' ')
                            setattr(event, 'date', date)
                            setattr(event, 'time', time)
                        else:
                            setattr(event, field, event_data[field])

                event.save()

            return redirect('profile', user_id=request.user.id)
    else:
        form = EventEditForm()
    return render(request, 'profile_edit.html', {'form': form})

def delete_card(request, event_id):
    if request.method == 'POST':
        buttonType = request.POST.get('buttonType')
        if buttonType == '削除':
            event = Event.objects.get(id=event_id)
            event.delete()
            return redirect('profile', user_id=request.user.id)
    else:
        return render(request, 'profile.html')
