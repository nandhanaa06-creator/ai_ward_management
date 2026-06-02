from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import chart_views

urlpatterns = [
    path('signup/',    views.signup,    name='signup'),
    path('login/',     views.user_login, name='login'),
    path('logout/',    auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-wards/', views.manage_wards, name='manage_wards'),
    path('manage-wards/<int:ward_id>/delete/', views.delete_ward, name='delete_ward'),
    path('manage-workers/', views.manage_workers, name='manage_workers'),
    path('citizens-list/', views.citizens_list, name='citizens_list'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('ward-report/', views.ward_performance_report, name='ward_performance_report'),
    
    # Chart API endpoints
    path('api/charts/complaints-per-ward/', chart_views.complaints_per_ward_data, name='chart_complaints_per_ward'),
    path('api/charts/monthly-complaints/', chart_views.monthly_complaints_data, name='chart_monthly_complaints'),
    path('api/charts/complaint-categories/', chart_views.complaint_categories_data, name='chart_complaint_categories'),
    path('api/charts/complaint-status/', chart_views.complaint_status_data, name='chart_complaint_status'),
]