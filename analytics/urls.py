from django.urls import path
from . import views

urlpatterns = [
    path('workers/', views.worker_analytics_dashboard, name='worker_analytics'),
    path('workers/<int:worker_id>/', views.worker_detail_analytics, name='worker_detail_analytics'),
    path('api/worker-comparison/', views.worker_comparison_chart, name='worker_comparison_chart'),
    path('api/worker-ratings/', views.worker_rating_chart, name='worker_rating_chart'),
    path('api/worker/<int:worker_id>/monthly/', views.worker_monthly_performance, name='worker_monthly_performance'),
    path('api/worker/<int:worker_id>/categories/', views.worker_category_breakdown, name='worker_category_breakdown'),
    path('workers/<int:worker_id>/export-pdf/', views.export_worker_performance_pdf, name='export_worker_pdf'),
]
