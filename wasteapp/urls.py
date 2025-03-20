from django.urls import path
from .views import get_bins, record_waste, dashboard, user_login, register, redeem_credits, edit_waste, delete_waste
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('', user_login, name='login'),  # Default page is login
    path('register/', register, name='register'),
    path('bins/', get_bins, name='bins'),
    path('record/', record_waste, name='record_waste'),
    path('dashboard/', dashboard, name='dashboard'),
    path('register/', register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),  # ✅ 
    path('redeem/', redeem_credits, name='redeem_credits'),  # ✅ Add redemption page
    path('edit-waste/<int:waste_id>/', edit_waste, name='edit_waste'),  # ✅ Edit Waste URL
    path('delete-waste/<int:waste_id>/', delete_waste, name='delete_waste'),
    
]
