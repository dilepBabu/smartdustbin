from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # ✅ Django default admin panel
    path('', include('wasteapp.urls')),  # ✅ Include all URLs from wasteapp
    path('accounts/', include('allauth.urls')),  # ✅ Authentication URLs
]
