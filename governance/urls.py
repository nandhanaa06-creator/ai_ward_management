from django.urls import path
from . import views

urlpatterns = [
    path('schedule/', views.schedule_meeting, name='schedule_meeting'),
    path('list/', views.meeting_list, name='meeting_list'),
]