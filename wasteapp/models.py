from django.db import models
from django.contrib.auth.models import User


from django.db import models
from django.contrib.auth.models import User
import firebase_admin
from firebase_admin import credentials, db
import threading
import time
from django.db.models.signals import pre_save
from django.dispatch import receiver
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
from django.db import models
from django.contrib.auth.models import User
import firebase_admin
from firebase_admin import credentials, db
import threading

# ✅ Initialize Firebase (Only Once)
if not firebase_admin._apps:
    cred = credentials.Certificate("C:\\Users\\dilep\\Desktop\\deep\\firebase_config.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://smart-dustbin-75385-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })

# ✅ Firebase Database Reference
firebase_ref = db.reference('/')

class WasteDisposalRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    barcode_id = models.CharField(max_length=100, null=True, blank=True)
    barcode_image = models.ImageField(upload_to='barcodes/', null=True, blank=True)
    waste_type = models.CharField(max_length=50)
    ir_sensor = models.BooleanField(default=False)  # ✅ IR Sensor Status
    credits_earned = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.barcode_id}"

    def update_firebase(self):
        """🔥 Update Firebase When Barcode is Uploaded"""
        if self.barcode_image:  # ✅ If barcode image is uploaded
            print("🔥 Barcode uploaded! Updating Firebase...")
            firebase_ref.update({"Ready": "start", "Status": True})  
            print("✅ Updated: Ready=start, Status=True")  

            def delayed_stop():
                import time
                time.sleep(15)
                print("⏳ 15s completed. Stopping...")
                firebase_ref.update({"Ready": "stop", "Status": False})
                print("✅ Updated: Ready=stop, Status=False")

            threading.Thread(target=delayed_stop, daemon=True).start()
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import WasteDisposalRecord
import firebase_admin
from firebase_admin import db
import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar  # ✅ Barcode Detection

# ✅ Firebase Reference
ref = db.reference('/')

def detect_barcode(image_path):
    """🚀 Detect Barcode from Image"""
    image = cv2.imread(image_path)
    barcodes = pyzbar.decode(image)
    
    if barcodes:
        return barcodes[0].data.decode('utf-8')  # ✅ Return detected barcode
    return None  # ❌ No barcode detected

def upload_barcode_image(request):
    """🔥 Upload Image & Auto-Fill Barcode ID"""
    if request.method == 'POST' and request.FILES.get('barcode_image'):
        barcode_image = request.FILES['barcode_image']

        # ✅ Save Temporary Image
        file_path = default_storage.save('temp/' + barcode_image.name, ContentFile(barcode_image.read()))
        full_path = default_storage.path(file_path)

        # 🔍 Detect Barcode
        detected_barcode = detect_barcode(full_path)

        if detected_barcode:
            print(f"✅ Barcode Detected: {detected_barcode}")
            return JsonResponse({'barcode_id': detected_barcode})  # ✅ Return to frontend
        
    return JsonResponse({'error': 'No barcode detected'}, status=400)

def submit_waste_disposal(request):
    """✅ Submit Waste Record & Update Firebase"""
    if request.method == 'POST':
        barcode_id = request.POST.get('barcode_id')
        barcode_image = request.FILES.get('barcode_image')

        if barcode_id:
            # ✅ Save Record in Database
            WasteDisposalRecord.objects.create(
                user=request.user, barcode_id=barcode_id, barcode_image=barcode_image
            )

            # ✅ Update Firebase (Ready: start)
            ref.update({"Ready": "start", "Status": True})
            print("🔥 Firebase Updated: Ready=start, Status=True")

            # ⏳ Auto Stop after 15s
            import threading
            def delayed_stop():
                import time
                time.sleep(15)
                ref.update({"Ready": "stop", "Status": False})
                print("✅ Firebase Updated: Ready=stop, Status=False")

            threading.Thread(target=delayed_stop, daemon=True).start()

    return redirect('record_waste_disposal')


class RedeemHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    redeemed_credits = models.IntegerField()
    reward = models.CharField(max_length=100)  # What the user redeemed for
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.reward} - {self.timestamp}"

