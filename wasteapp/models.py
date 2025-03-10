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

class WasteDisposal(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    bin = models.ForeignKey(WasteBin, on_delete=models.CASCADE)
    weight = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    credits_earned = models.IntegerField()

    def __str__(self):
        return f"{self.user.user.username} - {self.bin.location} - {self.credits_earned} credits"
