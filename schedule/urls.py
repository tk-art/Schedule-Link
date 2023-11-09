from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.top, name='top'),
    path('signup/', views.signup, name='signup'),
    path('login_view/', views.login_view, name='login_view'),
    path('logout_view/', views.logout_view, name='logout_view'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('profile_edit/', views.profile_edit, name='profile_edit'),
    path('follow/<int:user_id>/', views.follow, name='follow'),
    path('get_follow_status/<int:user_id>/', views.get_follow_status, name='get_follow_status'),
    path('calendar/', views.calendar, name='calendar'),
    path('api/calendar_events/<int:user_id>/', views.get_calendar_events, name='get_calendar_events'),
    path('get_event_data/<int:user_id>/', views.get_event_data, name='get_event_data'),
    path('delete_calendar/', views.delete_calendar, name='delete_calendar'),
    path('intentional_request/<int:user_id>/', views.intentional_request, name='intentional_request'),
    path('request_list/', views.request_list, name='request_list'),
    path('process_button/<int:user_id>/', views.process_button, name='process_button'),
    path('check_user_request/<int:user_id>/', views.check_user_request, name='check_user_request'),
    path('check_new_requests/', views.check_new_requests, name='check_new_requests'),
    path('mark_tab_as_read/', views.mark_tab_as_read, name='mark_tab_as_read'),
    path('chat/', views.chat, name='chat'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)