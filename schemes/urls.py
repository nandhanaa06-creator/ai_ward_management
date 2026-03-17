from django.urls import path
from . import views

urlpatterns = [
    path('match/', views.match_schemes, name='match_schemes'),
    path('eligible/', views.eligible_schemes, name='eligible_schemes'),
    path('create/', views.create_scheme, name='create_scheme'),
    path('notify/<int:scheme_id>/', views.notify_citizens, name='notify_citizens'),
]