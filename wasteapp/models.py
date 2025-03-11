from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    barcode_id = models.CharField(max_length=100, unique=True)  # Store scanned barcode
    credits = models.IntegerField(default=0)  # Default credits for new users

    def __str__(self):
        return self.user.username
class WasteBin(models.Model):
    bin_id = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=255)
    fill_level = models.FloatField(default=0.0)
    last_collected = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.location

class WasteDisposalRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    barcode_id = models.CharField(max_length=100, null=True, blank=True)
    barcode_image = models.ImageField(upload_to='barcodes/', null=True, blank=True)  # ✅ Store barcode image
    waste_type = models.CharField(max_length=50)
    credits_earned = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.waste_type} - {self.timestamp}"

