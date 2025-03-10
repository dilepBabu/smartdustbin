from django.contrib import admin
from .models import UserProfile, WasteBin, WasteDisposal

admin.site.register(UserProfile)
admin.site.register(WasteBin)
admin.site.register(WasteDisposal)
