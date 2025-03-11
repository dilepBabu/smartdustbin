from django.contrib import admin
from .models import UserProfile, WasteDisposalRecord

class WasteDisposalAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode_id', 'waste_type', 'credits_earned', 'timestamp')
    search_fields = ('name', 'barcode_id', 'waste_type')
    list_filter = ('waste_type', 'timestamp')

admin.site.register(UserProfile)
admin.site.register(WasteDisposalRecord, WasteDisposalAdmin)  # ✅ Registered waste records in admin panel
