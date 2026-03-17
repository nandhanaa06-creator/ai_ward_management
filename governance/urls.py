from django.urls import path
from . import views

urlpatterns = [
    path('schedule/', views.schedule_meeting, name='schedule_meeting'),
    path('list/', views.meeting_list, name='meeting_list'),
    path('detail/<int:pk>/', views.meeting_detail, name='meeting_detail'),
    path('publish-minutes/<int:pk>/', views.publish_minutes, name='publish_minutes'),
    path('rsvp/<int:pk>/', views.rsvp_meeting, name='rsvp_meeting'),
]