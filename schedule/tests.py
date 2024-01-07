from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, Calendar, UserRequest, UserResponse, ChatMessage, Profile, Event, Hobby, Interest
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from datetime import datetime, date, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
import json
from .forms import EventForm
from .views import recommendation_user_list, recommendation_event_list

class SignUpTest(TestCase):
    def setUp(self):
        app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='test_client_id',
            secret='test_secret'
        )
        site = Site.objects.get_current()
        app.sites.add(site)

    def test_valid_registration(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'email_conf': 'test@example.com',
            'password': 'testpassword',
            'password_conf': 'testpassword',
        })

        user = CustomUser.objects.get(username='testuser')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile', args=[user.id]))
        self.assertEqual(CustomUser.objects.count(), 1)

    def test_invalid_registration_email(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'email_conf': 'tests@example.com',
            'password': 'testpassword',
            'password_conf': 'testpassword',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'メールアドレスが一致しません')
        self.assertEqual(CustomUser.objects.count(), 0)

    def test_invalid_registration_password(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'email_conf': 'test@example.com',
            'password': 'testpaccword',
            'password_conf': 'testpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'パスワードが一致しません')
        self.assertEqual(CustomUser.objects.count(), 0)

class LoginTest(TestCase):
  def setUp(self):
      app = SocialApp.objects.create(
              provider='google',
              name='Google',
              client_id='test_client_id',
              secret='test_secret'
          )
      site = Site.objects.get_current()
      app.sites.add(site)

      self.user = CustomUser.objects.create_user(username='testuser', password='testpassword')

      image = SimpleUploadedFile(name='test_image.jpeg', content=b'', content_type='image/jpeg')

      Profile.objects.create(
          user=self.user, username='test1', age=20, gender="男性", residence="宮崎県", image=image
          )

  def test_login_success(self):
      response = self.client.post(reverse('login_view'), {
        'username': 'testuser',
        'password': 'testpassword'
      })
      user = CustomUser.objects.get(username='testuser')
      self.assertRedirects(response, reverse('profile', args=[user.id]))

  def test_login_fail(self):
      logged_in = self.client.login(username='testuser', password='tactpassword')
      response = self.client.post(reverse('login_view'), {
        'username': 'testuser',
        'password': 'tactpassword',
      })

      self.assertFalse(logged_in)
      self.assertContains(response, 'ユーザーネームかパスワードが違います、もう一度お試しください')

class LogoutTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    def test_logout(self):
        response = self.client.get(reverse('logout_view'))
        self.assertRedirects(response, reverse('top'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

class CalendarTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    def test_create_event(self):
        event_count = Calendar.objects.count()

        data = {
            'user': self.user.id,
            'free': 'Test Event',
            'selectedDate': '2023-11-01',
            'time': '13:00~15:00',
            'message': 'message'
        }

        url = reverse('calendar')
        response = self.client.post(url, data=data)

        self.assertEqual(Calendar.objects.count(), event_count + 1)

        new_event = Calendar.objects.latest('id')
        self.assertEqual(new_event.free, data['free'])
        self.assertEqual(new_event.time, data['time'])
        self.assertEqual(new_event.message, data['message'])

    def test_delete_event(self):
        Calendar.objects.create(
            user=self.user,
            selectedDate='2023-11-02',
            free='Test Event'
        )

        data = {
            'user_id': self.user.id,
            'deleteDate': '2023-11-02',
            'free': 'Test Event'
        }

        url = reverse('delete_calendar')
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Calendar.objects.count(), 0)

class UserRequestTests(TestCase):
    def setUp(self):
        self.user_a = CustomUser.objects.create_user('user_a', password='12345')
        self.user_b = CustomUser.objects.create_user('user_b', password='12345')

    def test_create_request(self):
        self.client.login(username='user_a', password='12345')
        response = self.client.post(reverse('intentional_request', args=[self.user_b.id]), {
            'userData': '2023-01-01',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserRequest.objects.filter(sender=self.user_a, receiver=self.user_b).exists())

    def test_check_new_requests(self):
        UserRequest.objects.create(sender=self.user_a, receiver=self.user_b, userData='2023-01-01', read=False)
        self.client.login(username='user_b', password='12345')
        response = self.client.get(reverse('check_new_requests'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['requests_unread'])

        UserRequest.objects.filter(receiver=self.user_b).update(read=True)
        response = self.client.get(reverse('check_new_requests'))
        self.assertFalse(response.json()['requests_unread'])

    def test_create_response(self):
        self.client.login(username='user_a', password='12345')
        self.client.post(reverse('intentional_request', args=[self.user_b.id]), {
            'userData': '2023-01-01',
        })

        self.client.get(reverse('logout_view'))
        self.client.login(username='user_b', password='12345')
        response = self.client.post(reverse('process_button', args=[self.user_a.id]), {
            'userData': '2023-01-01',
            'buttonType': '承認する'
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(UserResponse.objects.filter(sender=self.user_b, receiver=self.user_a).exists())

    def test_check_new_responses(self):
        UserRequest.objects.create(sender=self.user_a, receiver=self.user_b, userData='2023-01-01', read=False)
        UserResponse.objects.create(sender=self.user_b, receiver=self.user_a, userData='2023-01-01', buttonType="承認する", read=False)
        self.client.login(username='user_a', password='12345')
        response = self.client.get(reverse('check_new_requests'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['responses_unread'])

        UserResponse.objects.filter(receiver=self.user_a).update(read=True)
        response = self.client.get(reverse('check_new_requests'))
        self.assertFalse(response.json()['requests_unread'])

class ChatTests(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user('user_a', password='12345')
        self.user2 = CustomUser.objects.create_user('user_b', password='12345')
        self.client.login(username='user_a', password='12345')

        self.chat_message = ChatMessage.objects.create(
            sender=self.user1,
            receiver=self.user2,
            message="Hello, user2!",
            timestamp=datetime.now(),
            room_name= f'{self.user1.id}_{self.user2.id}',
            read=False
        )

    def test_message_sending(self):
        self.assertEqual(self.chat_message.sender, self.user1)
        self.assertEqual(self.chat_message.receiver, self.user2)
        self.assertEqual(self.chat_message.message, "Hello, user2!")

    def test_message_receiving(self):
        received_messages = ChatMessage.objects.filter(receiver=self.user2)
        self.assertIn(self.chat_message, received_messages)

    def test_chat_list_view(self):
        response = self.client.get(reverse('chat_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello, user2!")

    def test_chat_room_view(self):
        response = self.client.get(reverse('chat_room', kwargs={'user_id': self.user2.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello, user2!")

    def test_check_unread_messages_view(self):
        response = self.client.get(reverse('check_unread_messages', kwargs={'user_id': self.user2.id}))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'chat_unread': False})

    def test_mark_chat_as_read_view(self):
        response = self.client.get(reverse('mark_chat_as_read', kwargs={'user_id': self.user2.id}))
        self.assertEqual(response.status_code, 200)
        self.chat_message.refresh_from_db()
        self.assertTrue(self.chat_message.read)

class SearchTestCase(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user('user_a', password='12345')
        self.user2 = CustomUser.objects.create_user('user_b', password='12345')
        self.user3 = CustomUser.objects.create_user('user_c', password='12345')

        self.client.login(username='user_a', password='12345')
        self.search_url = reverse('search')

        image = SimpleUploadedFile(name='test_image.jpeg', content=b'', content_type='image/jpeg')

        Profile.objects.create(
            user=self.user1, username='test1', age=20, gender="男性", residence="宮崎県", image=image
            )
        Profile.objects.create(
            user=self.user2, username='test2', age=20, gender="男性", residence="宮崎県", image=image
            )
        Profile.objects.create(
            user=self.user3, username='test3', age=25, gender="女性", residence="宮崎県", image=image
            )

        Calendar.objects.create(user=self.user2, selectedDate=date.today() + timedelta(days=1), free="全日")



    def test_search_view_GET(self):
       response = self.client.get(self.search_url)
       self.assertEquals(response.status_code, 200)
       self.assertTemplateUsed(response, 'search.html')

    def test_search_Post(self):
        form_data = {
            'residence': '宮崎県',
            'gender': '男性',
            'min_age': 20,
            'max_age': 30
        }

        response = self.client.post(self.search_url, form_data)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'search_results.html')

    def test_search_view_POST_invalid(self):
        form_data = {
            'residence': '宮崎県',
            'gender': '男性',
            'min_age': 30,
            'max_age': 20
        }
        response = self.client.post(self.search_url, form_data)
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'search.html')
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())

    def test_not_include(self):
        form_data = {'residence': '宮崎県'}
        response = self.client.post(self.search_url, form_data)
        self.assertNotIn(self.user1, response.context['profiles'])

    def test_recent_free_time(self):
        form_data = {'residence': '宮崎県'}
        tomorrow = date.today() + timedelta(days=1)
        response = self.client.post(self.search_url, form_data)
        profiles = response.context['profiles']

        for profile in profiles:
            if profile.user == self.user2:
                self.assertEqual(profile.calendar, tomorrow)

class FollowerCountTest(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user('user_a', password='12345')
        self.user2 = CustomUser.objects.create_user('user_b', password='12345')

        self.client.login(username='user_a', password='12345')

        image = SimpleUploadedFile(name='test_image.jpeg', content=b'', content_type='image/jpeg')

        Profile.objects.create(
            user=self.user1, username='test1', age=20, gender="男性", residence="宮崎県", image=image
        )
        Profile.objects.create(
            user=self.user2, username='test2', age=20, gender="男性", residence="宮崎県", image=image
        )

    def test_new_follower(self):
        self.user2.profile.follows.add(self.user1.profile)
        self.assertEqual(self.user1.profile.followed_by.count(), 1)
        response = self.client.get(reverse('get_follower_count'))
        self.assertJSONEqual(str(response.content, encoding='utf8'), {'new_follower': True})

    def test_unfollowed(self):
        self.user2.profile.follows.add(self.user1.profile)

        response_confirm = self.client.get(reverse('confirm_followers_viewed'))
        self.assertEqual(self.client.session['last_follow_count'], 1)

        self.user2.profile.follows.remove(self.user1.profile)
        response_count = self.client.get(reverse('get_follower_count'))
        self.assertJSONEqual(str(response_count.content, encoding='utf8'), {'new_follower': False})
        self.assertEqual(self.client.session['last_follow_count'], 0)

class EventTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user('testuser', password='password')
        self.client.login(username='testuser', password='password')

        image = SimpleUploadedFile(name='test_image.jpeg', content=b'', content_type='image/jpeg')

        Profile.objects.create(
            user=self.user, username='testuser', age=20, gender="男性", residence="宮崎県", image=image
        )

        self.event = Event.objects.create(
            user=self.user,
            title='イベント',
            place='場所',
            date='2023-01-01',
            time='10:00~11:00',
            category='その他',
            image=image,
            detail='詳細情報'
        )

    def test_event_creation(self):
        with open('media/item_images/ルフィ.png', 'rb') as img:
            image = SimpleUploadedFile('ルフィ.png', img.read(), content_type='image/png')

        form_data = {
            'title': 'イベント',
            'place': '場所',
            'datetime': '2023-01-01 10:00~11:00',
            'category': 'その他',
            'detail': '詳細情報'
        }
        form_files = {'image': image}

        response = self.client.post(reverse('event'), form_data, **form_files)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Event.objects.count(), 2)

    def test_get_event_details(self):
        response = self.client.get(reverse('get_event_details'), {'event_id': self.event.id})
        response_data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['title'], 'イベント')

    def test_event_edit(self):
        form_data = {
            'title': 'タイトル編集',
            'place': '場所編集'
        }
        response = self.client.post(reverse('card_editing', args=(self.event.id,)), form_data)
        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, 'タイトル編集')
        self.assertEqual(self.event.place, '場所編集')

    def test_event_delete(self):
        response = self.client.post(reverse('delete_card', args=(self.event.id,)), {'buttonType': '削除'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Event.objects.count(), 0)

class AutoTest(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user('user_a', password='password')
        self.user2 = CustomUser.objects.create_user('user_b', password='password')
        self.user3 = CustomUser.objects.create_user('user_c', password='password')
        self.client.login(username='user_a', password='password')

        image = SimpleUploadedFile(name='test_image.jpeg', content=b'', content_type='image/jpeg')

        hobby1 = Hobby.objects.create(name='趣味1')
        hobby2 = Hobby.objects.create(name='趣味2')

        self.profile1 = Profile.objects.create(
            user=self.user1, username='user_a', age=20, gender="男性", residence="宮崎県", image=image
        )

        self.profile2 = Profile.objects.create(
            user=self.user2, username='user_b', age=20, gender="男性", residence="宮崎県", image=image
        )

        self.profile1.hobby.set([hobby1, hobby2])
        self.profile2.hobby.set([hobby2])

        self.profile1.follows.add(self.profile2)

        today_date = datetime.now().date()
        self.calendar1 = Calendar.objects.create(user=self.user1, selectedDate=today_date)
        self.calendar2 = Calendar.objects.create(user=self.user2, selectedDate=today_date)
        self.calendar3 = Calendar.objects.create(user=self.user3, selectedDate=today_date)

        self.event1 = Event.objects.create(
            user=self.user2,
            title='イベント',
            place='場所',
            date=today_date,
            time='10:00~11:00',
            category='その他',
            image=image,
            detail='詳細情報'
        )

        self.event2 = Event.objects.create(
            user=self.user3,
            title='イベント',
            place='場所',
            date=today_date,
            time='10:00~11:00',
            category='その他',
            image=image,
            detail='詳細情報'
        )

    def test_get_recommendation_user_list(self):
        response = self.client.get(reverse('top') + '?recommend_user=おすすめユーザー')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user2, response.context['users'])
        self.assertNotIn(self.user3, response.context['users'])
        self.assertIn(self.calendar2.selectedDate, response.context['user_first_match'].values())

    def test_get_recommendation_event_list(self):
        response = self.client.get(reverse('top') + '?recommend_event=おすすめイベント')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.event1, response.context['matched_events'])
        self.assertNotIn(self.event2, response.context['matched_events'])
