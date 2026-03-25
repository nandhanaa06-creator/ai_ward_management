from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('export/complaints-excel/', views.export_complaints_excel, name='export_complaints_excel'),
    path('export/schemes-excel/', views.export_schemes_excel, name='export_schemes_excel'),
    path('export/monthly-pdf/', views.export_monthly_report_pdf, name='export_monthly_pdf'),
]
