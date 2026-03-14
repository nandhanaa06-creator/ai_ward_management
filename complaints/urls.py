from django.urls import path
from . import views

urlpatterns = [
    path('report/', views.report_complaint, name='report_complaint'),
    path('list/', views.complaint_list, name='complaint_list'),
    path('<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('<int:complaint_id>/resolve/', views.resolve_issue, name='resolve_issue'),
    path('<int:complaint_id>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('<int:complaint_id>/message/', views.post_complaint_message, name='post_complaint_message'),
    path('<int:complaint_id>/reassign/', views.reassign_worker, name='reassign_worker'),
]