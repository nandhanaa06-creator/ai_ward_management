from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.notification_list, name='notification_list'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('mark-read/<int:notification_id>/', views.mark_read, name='mark_read'),
    path('unread-count/', views.unread_count, name='unread_count'),
]
