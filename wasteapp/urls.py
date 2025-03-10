from django.urls import path
from .views import get_bins, record_waste, dashboard, user_login, register

urlpatterns = [
    path('', user_login, name='login'),  # Default page is login
    path('register/', register, name='register'),
    path('bins/', get_bins, name='bins'),
    path('record/', record_waste, name='record_waste'),
    path('dashboard/', dashboard, name='dashboard'),
    path('accounts/register/', register, name='register'),
]
