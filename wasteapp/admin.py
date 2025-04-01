from django.contrib import admin
from .models import UserProfile, WasteDisposalRecord


class WasteDisposalAdmin(admin.ModelAdmin):
    list_display = ('user', 'barcode_id', 'waste_type', 'credits_earned', 'timestamp')  # ✅ Correct fields
    search_fields = ('user__username', 'barcode_id', 'waste_type')
    list_filter = ('waste_type', 'timestamp')

admin.site.register(UserProfile)
admin.site.register(WasteDisposalRecord, WasteDisposalAdmin)  # ✅ Registered waste records in admin panel
