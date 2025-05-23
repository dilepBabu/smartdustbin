from django.db import models
from django.contrib.auth.models import User


from django.db import models
from django.contrib.auth.models import User
import firebase_admin
from firebase_admin import credentials, db
import threading
import time
from django.db.models.signals import pre_save, post_save
from django.db.models import Sum
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    barcode_id = models.CharField(max_length=100, unique=True)
    credits = models.IntegerField(default=0, null=False, blank=False)  
    total_credits = models.IntegerField(default=0)  


    def __str__(self):
        return f"{self.user.username} - {self.total_credits}"
class WasteBin(models.Model):
    bin_id = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=255)
    fill_level = models.FloatField(default=0.0)
    last_collected = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.location
from django.db import models
from django.contrib.auth.models import User
import firebase_admin
from firebase_admin import credentials, db
import threading


if not firebase_admin._apps:
    cred = credentials.Certificate("C:\\Users\\dilep\\Desktop\\deep\\firebase_config.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://smart-dustbin-75385-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })


firebase_ref = db.reference('/')

class WasteDisposal(models.Model):  
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=100, unique=True, null=True, blank=True) 
    barcode_image = models.ImageField(upload_to='barcodes/', null=True, blank=True)    
    waste_type = models.CharField(max_length=50)
    ir_sensor = models.BooleanField(default=False)
    credits_earned = models.IntegerField(default=0)    
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
       
        user_profile, created = UserProfile.objects.get_or_create(user=self.user)
        
        user_profile.total_credits = WasteDisposal.objects.filter(user=self.user).aggregate(total=Sum('credits_earned'))['total'] or 0
        user_profile.save()

    def update_firebase(self):
        """🔥 Update Firebase When Barcode is Uploaded"""
        if self.barcode_image:
            print("🔥 Barcode uploaded! Updating Firebase...")
            firebase_ref.update({"Ready": "start", "Status": True})  
            print("✅ Updated: Ready=start, Status=True")  

            def delayed_stop():
                time.sleep(15)
                print("⏳ 15s completed. Stopping...")
                firebase_ref.update({"Ready": "stop", "Status": False})
                print("✅ Updated: Ready=stop, Status=False")

            threading.Thread(target=delayed_stop, daemon=True).start()


def update_user_credits(user):
    """Update total credits for a user in UserProfile"""
    total_credits = WasteDisposal.objects.filter(user=user).aggregate(total_credits=Sum('credits_earned'))
    total_credits = total_credits.get('total_credits', 0) or 0
    user_profile = UserProfile.objects.get(user=user)
    user_profile.total_credits = total_credits
    user_profile.save()


from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import WasteDisposal  

import firebase_admin
from firebase_admin import db
import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar  


ref = db.reference('/')

def detect_barcode(image_path):
    """🚀 Detect Barcode from Image"""
    image = cv2.imread(image_path)
    barcodes = pyzbar.decode(image)
    
    if barcodes:
        return barcodes[0].data.decode('utf-8') 
    return None  

def upload_barcode_image(request):
    """🔥 Upload Image & Auto-Fill Barcode ID"""
    if request.method == 'POST' and request.FILES.get('barcode_image'):
        barcode_image = request.FILES['barcode_image']
        file_path = default_storage.save('temp/' + barcode_image.name, ContentFile(barcode_image.read()))
        full_path = default_storage.path(file_path)

        
        detected_barcode = detect_barcode(full_path)

        if detected_barcode:
            return JsonResponse({'barcode_id': detected_barcode})  
        
    return JsonResponse({'error': 'No barcode detected'}, status=400)

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import WasteDisposal
import threading
import time

@login_required
def submit_waste_disposal(request):
    """✅ Submit Waste Record & Update Firebase"""
    if request.method == 'POST':
        barcode_id = request.POST.get('barcode_id')
        barcode_image = request.FILES.get('barcode_image')
        credits_earned = 5  

        if barcode_id:
            
            WasteDisposal.objects.create(
                user=request.user,
                barcode=barcode_id,  
                barcode_image=barcode_image,
                credits_earned=credits_earned  
            )

           
            ref.update({"Ready": "start", "Status": True})
            print("🔥 Firebase Updated: Ready=start, Status=True")

           
            def delayed_stop():
                time.sleep(15)
                ref.update({"Ready": "stop", "Status": False})
                print("✅ Firebase Updated: Ready=stop, Status=False")

            threading.Thread(target=delayed_stop, daemon=True).start()

    return redirect('record_waste_disposal')



class Redemption(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    redeemed_credits = models.IntegerField()
    reward = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.reward} - {self.timestamp}"

from django.db import models
from django.contrib.auth.models import User

class RedeemHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reward = models.CharField(max_length=255)
    credits_used = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.reward}"
