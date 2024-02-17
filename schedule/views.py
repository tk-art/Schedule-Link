from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from .forms import SignupForm, ProfileForm, CalendarForm, SearchForm, EventForm, EventEditForm
from .models import CustomUser, Profile, Calendar, UserRequest, UserResponse, ChatMessage, Notification, Event
from django.shortcuts import redirect
from django.http import JsonResponse
import json
from django.core.serializers import serialize
from django.contrib import messages
import pytz
import os
from django.conf import settings
from datetime import datetime, date, timedelta
from django.db import models
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Count

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

def approved_events_function(user_id):
    approved_events = []
    approved_data = []
    if user_id:
        user_response = UserResponse.objects.filter(sender=user_id, buttonType="承認する")
        for response in user_response:
            if response.eventId:
                approved_events.append(response.eventId_id)
            if response.userData:
                approved_data.append(response.userData)

        approved_data_as_strings = [date_obj.strftime('%Y-%m-%d') for date_obj in approved_data]
    else:
        user_response = UserResponse.objects.filter(buttonType="承認する")
        for response in user_response:
            if response.eventId:
                approved_events.append(response.eventId_id)
            if response.userData:
                approved_data.append(response.userData)

        approved_data_as_strings = [date_obj.strftime('%Y-%m-%d') for date_obj in approved_data]

    return approved_events, approved_data_as_strings

def top(request):
    category = request.GET.get('category', '')
    recommend_user = request.GET.get('recommend_user', '')
    recommend_event = request.GET.get('recommend_event', '')
    situation = request.GET.get('situation', '')

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

    approved_events, approved_data = approved_events_function(None)

    situation_list = []
    if situation == '確定済み':
        for approved_event in approved_events:
            event = Event.objects.get(id=approved_event)
            situation_list.append(event)
    elif situation == '未確定':
        events = Event.objects.all()
        for event in events:
            if event.id not in approved_events:
                situation_list.append(event)
    else:
        sorted_situation_list = None

    if situation_list:
        sorted_situation_list = sorted(situation_list, key=lambda x: x.timestamp, reverse=True)

    if sorted_situation_list:
        for event in sorted_situation_list:
            event.delta = human_readable_time_from_utc(event.timestamp)
    else:
        for event in events:
            event.delta = human_readable_time_from_utc(event.timestamp)

    context = {
        'events': events,
        'users': users,
        'user_first_match': user_first_match,
        'matched_events': matched_events,
        'approved_events': approved_events,
        'situation_list': sorted_situation_list
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

            Profile.objects.create(
                user=user, username=username, content='これはデフォルトのプロフィールです。好みに応じて編集してください'
            )

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

def guest_login(request):
    guest_user = CustomUser.objects.create_user(username='ゲストユーザー{}'.format(CustomUser.objects.count()), is_guest=True)
    large_number_of_events_user = CustomUser.objects.annotate(num_events=Count('event')).order_by('-num_events').first()
    sender_last_event = Event.objects.filter(user=large_number_of_events_user).last()
    room_name = f'{min(guest_user.id, large_number_of_events_user.id)}_{max(guest_user.id, large_number_of_events_user.id)}'
    selectedDate = date.today() + timedelta(days=1)

    Profile.objects.create(user=guest_user, username=guest_user.username,
        content='これはデフォルトのプロフィールです。好みに応じて編集してください'
    )

    if settings.DEBUG:
        event = Event.objects.create(
            user=guest_user, title='テスト', place='テスト', category='その他',
            date=date.today() + timedelta(days=1), time='10:00~10:30',
            image='item_images/フリー女.jpeg', detail='テスト'
        )
    else:
        event = Event.objects.create(
            user=guest_user, title='テスト', place='テスト', category='その他',
            date=selectedDate, time='10:00~10:30',
            image='media/item_images/neko', detail='テスト'
        )

    Calendar.objects.create(
        user=guest_user, selectedDate=selectedDate, free="全日"
    )
    Calendar.objects.create(
        user=guest_user, selectedDate=date.today() + timedelta(days=2), free="全日"
    )

    UserRequest.objects.create(
        sender=large_number_of_events_user, receiver=guest_user, userData=None, eventId_id=event.id, situation=True
    )
    UserRequest.objects.create(
      sender=large_number_of_events_user, receiver=guest_user, userData=selectedDate, eventId_id=None, situation=True
    )

    UserResponse.objects.create(
        sender=large_number_of_events_user, receiver=guest_user, userData=None, eventId=sender_last_event, buttonType='承認する'
    )

    ChatMessage.objects.create(
        sender=guest_user, receiver=large_number_of_events_user, message='初めまして！', room_name=room_name, read=True
    )

    guest_user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, guest_user)
    return redirect('profile', user_id=guest_user.id)

def logout_view(request):
    user = request.user
    if user.is_guest:
        user.delete()
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

    approved_events, approved_data = approved_events_function(profile.user)

    context = {
        'profile': profile,
        'hobbies': hobbies,
        'interests': interests,
        'follows': follows,
        'followers': followers,
        'current_user': current_user,
        'events': events,
        'approved_events': approved_events,
        'approved_data': approved_data,
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

# リクエスト

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

    context = {
        'request_users': request_users,
        'response_users': response_users,
        'current_user': current_user,
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

    #　mathing_users = 同じ県でフォローしているユーザ　＋　同じ県で趣味、興味に共通点があるユーザ
    matching_users = get_matching_profiles(current_user)
    print(matching_users)

    #　暇な時間が被っているユーザを取得
    user_first_match = {}
    for user_free_time in user_free_times:
        matched_users = Calendar.objects.filter(
            selectedDate=user_free_time.selectedDate
        ).exclude(user=current_user)

        for matched_user in matched_users:
            user_id = matched_user.user.id
            if user_id not in user_first_match:
                user_first_match[user_id] = matched_user.selectedDate

    #　暇な時間がマッチしたユーザーのidだけをリスト化
    first_matched_users = list(user_first_match.keys())

    # = 暇な時間が一致しているユーザかつmathing_usersをリスト化
    final_matched_users = list(set(first_matched_users) & set(matching_users))

    #　final_matched_users リストにリストされている順番と同じ順序でユーザーオブジェクトを並べ替え
    users = sorted(CustomUser.objects.filter(id__in=final_matched_users), key=lambda u: final_matched_users.index(u.id))
    return users, user_first_match

def recommendation_event_list(request):
    current_user = request.user
    today_date = datetime.now().date()
    user_free_times = Calendar.objects.filter(user=current_user, selectedDate__gte=today_date)

    #　mathing_users = 同じ県でフォローしているユーザ　＋　同じ県で趣味、興味に共通点があるユーザ
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

def invitation_request(request, event_id):
    if request.method == 'POST':
        selected_users = request.POST.get('selectedUsers')
        selected_users = json.loads(selected_users)
        for selected_user in selected_users:
            user = CustomUser.objects.get(id=selected_user)
            UserRequest.objects.create(sender=request.user, receiver=user, userData=None, eventId_id=event_id, situation=True)

    return JsonResponse({'status': 'success'})

# レスポンス

def process_button(request, user_id):
    if request.method == 'POST':
        sender = request.user
        receiver = CustomUser.objects.get(id=user_id)
        userData = request.POST.get('userData')
        buttonType = request.POST.get('buttonType')
        if request.POST.get('eventId'):
            event_id = int(request.POST.get('eventId'))
            eventId = Event.objects.get(id=event_id)
        else:
            eventId = None

        UserResponse.objects.create(sender=sender, receiver=receiver, userData=userData, eventId=eventId, buttonType=buttonType)

        if eventId:
            user_request = UserRequest.objects.get(sender=receiver, receiver=sender, eventId=eventId, is_processed=False)
        else:
            user_request = UserRequest.objects.get(sender=receiver, receiver=sender, userData=userData, is_processed=False)
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

#　チャット

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
            room_info['sender'] = last_room.sender
        else:
            room_info['receiver'] = last_room.sender
            room_info['sender'] = last_room.sender
        rooms_receiver.append(room_info)

    rooms_receiver_sorted = sorted(rooms_receiver, key=lambda x: x['timestamp'], reverse=True)
    return render(request, 'chat_list.html', {'rooms': rooms_receiver_sorted})


def chat_room(request, user_id):
    other_user = CustomUser.objects.get(id=user_id)
    current_user = request.user
    room_name = f'{min(current_user.id, other_user.id)}_{max(current_user.id, other_user.id)}'
    chat_messages = ChatMessage.objects.filter(room_name=room_name)

    sender_last_message = None
    if chat_messages and chat_messages.last().sender == current_user:
        sender_last_message = chat_messages.last()

    for chat in chat_messages:
        chat.delta = human_readable_time_from_utc(chat.timestamp)

    context = {
        'current_user': current_user,
        'other_user': other_user,
        'room_name': room_name,
        'chat_messages': chat_messages,
        'sender_last_message': sender_last_message
    }

    return render(request, 'chat.html', context)

def check_unread_full_messages(request):
    chat_unread = ChatMessage.objects.filter(receiver=request.user, read=False)
    sender_ids = chat_unread.values_list('sender_id', flat=True).distinct()


    response = {
        'chat_unread': chat_unread.exists(),
        'sender_ids': sender_ids
    }
    return JsonResponse(response)

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
    last_message = ChatMessage.objects.filter(room_name=room_name).last()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{last_message.sender_id}',
        {
            'type': 'send_read_receipt',
            'message_id': last_message.id
        }
    )

    return JsonResponse({'status': 'success'})

# 検索

@login_required
def search(request):
    ages = list(range(18, 51))
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            date_search = form.cleaned_data.get('date_search')
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

            matching_profiles = []
            matching_events = []
            approved_events, approved_data = approved_events_function(None)
            if date_search:
                if '~' in date_search:
                    start_str, end_str = date_search.split('~')
                    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                    end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
                    end_date += timedelta(days=1)
                    for profile in profiles:
                        if Calendar.objects.filter(user_id=profile.user.id, selectedDate__range=(start_date, end_date)).exists():
                            matching_profiles.append(profile)

                        events = Event.objects.filter(user_id=profile.user.id, date__range=(start_date, end_date))
                        for event in events:
                            if event.id not in approved_events:
                                event.delta = human_readable_time_from_utc(event.timestamp)
                                matching_events.append(event)
                    profiles = None
                else:
                    for profile in profiles:
                        if Calendar.objects.filter(user_id=profile.user.id, selectedDate=date_search).exists():
                            matching_profiles.append(profile)

                        events = Event.objects.filter(user_id=profile.user.id, date=date_search)
                        for event in events:
                            if event.id not in approved_events:
                                event.delta = human_readable_time_from_utc(event.timestamp)
                                matching_events.append(event)
                    profiles = None

            matching_events_sorted = sorted(matching_events, key=lambda x: x.timestamp, reverse=True)

            if matching_profiles or matching_events:
                return render(request, 'search_results.html', {'profiles' : matching_profiles, 'events': matching_events_sorted, 'approved_events': approved_events})
            elif profiles:
                return render(request, 'search_results.html', {'profiles' : profiles})
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

# イベント作成

def event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data.get('title')
            image = form.cleaned_data.get('image')
            if image == None:
                if settings.DEBUG:
                    image = 'item_images/フリー女.jpeg'
                else:
                    image = 'media/item_images/neko'
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

def invitation_user(request, event_id):
    event = Event.objects.get(id=event_id)
    user_free_times = Calendar.objects.filter(selectedDate=event.date).exclude(user=request.user)
    already_exists_requests = UserRequest.objects.filter(sender=request.user, eventId=event).values_list('receiver', flat=True)

    invitation_users = []
    for user_free_time in user_free_times:
        user = user_free_time.user
        if not user.id in already_exists_requests:
            user_info = {
                'id': user.id,
                'username': user.profile.username,
                'image_url': user.profile.image.url
            }
            invitation_users.append(user_info)

    return JsonResponse({'invitation_users': invitation_users})
