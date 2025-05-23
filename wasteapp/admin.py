from django.contrib import admin
from .models import UserProfile, WasteDisposal
from wasteapp.models import WasteDisposal


class WasteDisposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'waste_type')  
    search_fields = ('user__username', 'barcode', 'waste_type')
    list_filter = ('waste_type', 'timestamp')

admin.site.register(UserProfile)
admin.site.register(WasteDisposal, WasteDisposalAdmin)  
