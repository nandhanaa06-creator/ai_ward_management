from django.urls import path
from . import views

urlpatterns = [
    path('manage/', views.manage_surveys, name='manage_surveys'),
    path('create/', views.create_survey, name='create_survey'),
    path('edit/<int:survey_id>/', views.create_survey, name='edit_survey'),
    path('delete/<int:survey_id>/', views.delete_survey, name='delete_survey'),
    path('s/<slug:slug>/', views.render_survey, name='render_survey'),
    path('submissions/<int:survey_id>/', views.survey_submissions, name='survey_submissions'),
]
