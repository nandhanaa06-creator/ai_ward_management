from django.urls import path
from . import views

urlpatterns = [
    path('match/', views.match_schemes, name='match_schemes'),
    path('eligible/', views.eligible_schemes, name='eligible_schemes'),  # backwards-compat redirect
]