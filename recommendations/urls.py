from django.urls import path
from . import views

urlpatterns = [
    # Citizen views
    path('my-recommendations/', views.citizen_recommendations, name='citizen_recommendations'),
    path('refresh/', views.refresh_recommendations, name='refresh_recommendations'),
    path('mark-viewed/<int:rec_id>/', views.mark_recommendation_viewed, name='mark_recommendation_viewed'),
    path('mark-applied/<int:rec_id>/', views.mark_recommendation_applied, name='mark_recommendation_applied'),
    
    # Admin views
    path('analytics/', views.admin_recommendation_analytics, name='admin_recommendation_analytics'),
    
    # API endpoints
    path('api/score-distribution/', views.recommendation_score_distribution, name='recommendation_score_distribution'),
    path('api/conversion-funnel/', views.recommendation_conversion_funnel, name='recommendation_conversion_funnel'),
]
