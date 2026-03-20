from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('signup/',    views.signup,    name='signup'),
    path('login/',     auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/',    auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-wards/', views.manage_wards, name='manage_wards'),
    path('manage-workers/', views.manage_workers, name='manage_workers'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('ward-report/', views.ward_performance_report, name='ward_performance_report'),
]