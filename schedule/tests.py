from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, Calendar, UserRequest, UserResponse
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


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
        self.assertRedirects(response, reverse('top'))
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

  def test_login_success(self):
      logged_in = self.client.login(username='testuser', password='testpassword')
      self.assertTrue(logged_in)

      response = self.client.get(reverse('top'))
      self.assertEqual(response.status_code, 200)

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
        # テスト用のユーザーを作成
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
