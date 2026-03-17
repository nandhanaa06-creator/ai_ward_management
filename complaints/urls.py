from django.urls import path
from . import views

urlpatterns = [
    path('report/', views.report_complaint, name='report_complaint'),
    path('list/', views.complaint_list, name='complaint_list'),
    path('<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('<int:complaint_id>/resolve/', views.complete_task, name='complete_task'),
    path('<int:complaint_id>/task-detail/', views.worker_task_detail, name='worker_task_detail'),
    path('<int:complaint_id>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('<int:complaint_id>/message/', views.post_complaint_message, name='post_complaint_message'),
    path('<int:complaint_id>/reassign/', views.reassign_worker, name='reassign_worker'),
    path('<int:duplicate_id>/merge/', views.merge_complaint, name='merge_complaint'),
    path('<int:complaint_id>/suggest-worker/', views.suggest_worker, name='suggest_worker'),
]