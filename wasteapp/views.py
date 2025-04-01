from django.shortcuts import render, redirect,get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WasteBin, WasteDisposalRecord, UserProfile, RedeemHistory
from django.contrib.auth import authenticate, login, logout,authenticate, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone  # ✅ Import timezone for timestamp
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image
from .forms import WasteDisposalForm
@api_view(['GET'])
def get_bins(request):
    bins = WasteBin.objects.all().values()
    return Response({'bins': list(bins)})
@login_required
def record_waste(request):
    if request.method == 'POST':
        form = WasteDisposalForm(request.POST, request.FILES)
        barcode_value = request.POST.get('barcode', '')  # ✅ Get scanned barcode

        if form.is_valid():
            try:
                # ✅ Check if the barcode exists in the UserProfile table
                user_profile = UserProfile.objects.get(barcode_id=barcode_value)

                # ✅ Ensure that waste is recorded for the correct user (not the logged-in user by default)
                waste_disposal = form.save(commit=False)
                waste_disposal.user = user_profile.user  # ✅ Assign waste to the correct user
                waste_disposal.barcode_id = barcode_value
                waste_disposal.credits_earned = 5
                waste_disposal.timestamp = timezone.now()
                waste_disposal.save()

                # ✅ Add credits only to the correct user
                user_profile.credits += 5
                user_profile.save()

                messages.success(request, f"Waste recorded successfully for {user_profile.user.username}!")
                return redirect('dashboard')

            except UserProfile.DoesNotExist:
                messages.error(request, "This barcode is not registered. Please use a valid barcode.")
                return redirect('record_waste')

    else:
        form = WasteDisposalForm()

    return render(request, 'wasteapp/record_waste.html', {'form': form})



def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'wasteapp/login.html')



def user_logout(request):
    logout(request)
    return redirect('login')
@login_required
def dashboard(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)

        # ✅ Show only the logged-in user's records
        disposal_history = WasteDisposalRecord.objects.filter(user=request.user).order_by('-timestamp')
        redemption_history = RedeemHistory.objects.filter(user=request.user).order_by('-timestamp')

        context = {
            'username': request.user.username,
            'barcode_id': user_profile.barcode_id,
            'total_credits': user_profile.credits,
            'disposal_history': disposal_history,  # ✅ Now only shows user's own records
            'redemption_history': redemption_history,
        }
        return render(request, 'wasteapp/dashboard.html', context)

    except UserProfile.DoesNotExist:
        messages.error(request, "Your profile is incomplete. Please contact the admin.")
        return redirect('logout')



def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        barcode_id = request.POST['barcode_id']

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        if UserProfile.objects.filter(barcode_id=barcode_id).exists():
            messages.error(request, "This barcode is already registered!")
            return redirect('register')

        user = User.objects.create_user(username=username, password=password1)
        UserProfile.objects.create(user=user, barcode_id=barcode_id)

        # Explicitly set authentication backend
        backend = get_backends()[0]  # Select the first authentication backend
        user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
        
        login(request, user)  # Now Django knows which backend to use

        messages.success(request, "Registration successful!")
        return redirect('dashboard')

    return render(request, 'wasteapp/register.html')

@login_required
def record_waste(request):
    if request.method == 'POST':
        form = WasteDisposalForm(request.POST, request.FILES)
        barcode_value = request.POST.get('barcode', '')  # Get scanned barcode

        if form.is_valid():
            try:
                # ✅ Find the user that owns this barcode
                user_profile = UserProfile.objects.get(barcode_id=barcode_value)

                # ✅ Create a new waste record under the correct user
                waste_disposal = form.save(commit=False)
                waste_disposal.user = user_profile.user  # ✅ Assign waste to the correct user
                waste_disposal.barcode_id = barcode_value
                waste_disposal.credits_earned = 5
                waste_disposal.timestamp = timezone.now()
                waste_disposal.save()

                # ✅ Update credits for the correct user
                user_profile.credits += 5
                user_profile.save()

                messages.success(request, f"Waste disposal recorded successfully for {user_profile.user.username}!")
                return redirect('dashboard')

            except UserProfile.DoesNotExist:
                messages.error(request, "This barcode is not registered. Please use a valid barcode.")
                return redirect('record_waste')

    else:
        form = WasteDisposalForm()

    return render(request, 'wasteapp/record_waste.html', {'form': form})


# ✅ Function to extract barcode from an uploaded image
def extract_barcode_from_image(image):
    img = Image.open(image)
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)  # Convert to grayscale
    barcodes = decode(img)

    if barcodes:
        return barcodes[0].data.decode('utf-8')  # ✅ Return the barcode as text
    return None  # ✅ Return None if no barcode is detected

from .forms import RedeemForm

@login_required
def redeem_credits(request):
    user_profile = UserProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = RedeemForm(request.POST)
        if form.is_valid():
            selected_reward = form.cleaned_data['reward']
            required_credits = 70 if selected_reward == 'Sick Leave' else 50  # Set credit requirement

            if user_profile.credits >= required_credits:
                # Deduct credits and save redemption history
                user_profile.credits -= required_credits
                user_profile.save()

                RedeemHistory.objects.create(
                    user=request.user,
                    redeemed_credits=required_credits,
                    reward=selected_reward
                )

                messages.success(request, f"You have successfully redeemed {selected_reward}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Not enough credits to redeem this reward.")
    
    else:
        form = RedeemForm()

    return render(request, 'wasteapp/redeem.html', {'form': form, 'credits': user_profile.credits})


@login_required
def edit_waste(request, waste_id):
    waste_record = get_object_or_404(WasteDisposalRecord, id=waste_id, user=request.user)

    if request.method == "POST":
        form = WasteDisposalForm(request.POST, instance=waste_record)
        if form.is_valid():
            form.save()
            messages.success(request, "Waste record updated successfully!")
            return redirect('dashboard')
    else:
        form = WasteDisposalForm(instance=waste_record)

    return render(request, 'wasteapp/edit_waste.html', {'form': form})

@login_required
def delete_waste(request, waste_id):
    waste_record = get_object_or_404(WasteDisposalRecord, id=waste_id, user=request.user)
    waste_record.delete()
    messages.success(request, "Waste record deleted successfully!")
    return redirect('dashboard')


from django.db.models import Q
from django.utils.dateparse import parse_date

def admin_required(user):
    return user.is_staff

@user_passes_test(admin_required, login_url='/login/')
def admin_dashboard(request):
    users = UserProfile.objects.all()
    waste_records = WasteDisposalRecord.objects.all()

    # Fetch filter parameters from request
    search_query = request.GET.get('search', '')
    waste_type_filter = request.GET.get('waste_type', '')
    start_date = parse_date(request.GET.get('start_date', ''))
    end_date = parse_date(request.GET.get('end_date', ''))

    # Apply filters
    if search_query:
        waste_records = waste_records.filter(
            Q(user__username__icontains=search_query) |
            Q(barcode_id__icontains=search_query)
        )

    if waste_type_filter:
        waste_records = waste_records.filter(waste_type=waste_type_filter)

    if start_date:
        waste_records = waste_records.filter(timestamp__date__gte=start_date)

    if end_date:
        waste_records = waste_records.filter(timestamp__date__lte=end_date)

    # Get unique waste types for dropdown
    waste_types = WasteDisposalRecord.objects.values_list('waste_type', flat=True).distinct()

    context = {
        "users": users,
        "waste_records": waste_records,
        "waste_types": waste_types
    }
    return render(request, "wasteapp/admin_dashboard.html", context)

from django.http import JsonResponse
import firebase_admin
from firebase_admin import db

def start_waste_disposal(request):
    if request.method == "POST":
        barcode = request.POST.get("barcode")  # Get barcode from request

        if barcode:
            ref = db.reference("waste_status")  # Firebase database reference
            ref.update({
                "ready": "start",  # Update status to "start"
                "status": True  # IR sensor should start detecting
            })
            return JsonResponse({"message": "Waste disposal started", "status": "success"})

    return JsonResponse({"message": "No barcode provided", "status": "error"})


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import WasteDisposalRecord

@login_required
def upload_waste(request):
    """📌 Handle New Waste Upload"""
    if request.method == "POST":
        barcode_image = request.FILES.get('barcode_image')

        if barcode_image:
            waste_entry = WasteDisposalRecord.objects.create(
                user=request.user,
                barcode_image=barcode_image,
                waste_type=request.POST.get('waste_type', 'unknown'),
                ir_sensor=True  # ✅ Start IR sensor when waste is added
            )
            waste_entry.save()
            return redirect('waste_success')  # ✅ Redirect to a success page

    return render(request, "upload_waste.html")
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import WasteDisposalRecord
import firebase_admin
from firebase_admin import credentials, db
import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar  # ✅ Barcode detection

# ✅ Firebase Reference
ref = db.reference('/')

def detect_barcode(image_path):
    """🚀 Detect Barcode from Image"""
    image = cv2.imread(image_path)
    barcodes = pyzbar.decode(image)
    
    if barcodes:
        return barcodes[0].data.decode('utf-8')  # ✅ Return detected barcode
    return None  # ❌ No barcode detected

def upload_barcode(request):
    """🔥 Upload Barcode & Detect It"""
    if request.method == 'POST' and request.FILES.get('barcode_image'):
        barcode_image = request.FILES['barcode_image']

        # ✅ Save Temporary Image
        file_path = default_storage.save('temp/' + barcode_image.name, ContentFile(barcode_image.read()))
        full_path = default_storage.path(file_path)

        # 🔍 Detect Barcode
        detected_barcode = detect_barcode(full_path)

        if detected_barcode:
            print(f"✅ Barcode Detected: {detected_barcode}")

            # ✅ Update Firebase Only When Barcode is Read
            ref.update({"Ready": "start", "Status": True})
            print("🔥 Firebase Updated: Ready=start, Status=True")

            # ⏳ Stop After 15 Seconds
            import threading
            def delayed_stop():
                import time
                time.sleep(15)
                print("⏳ 15s completed. Stopping...")
                ref.update({"Ready": "stop", "Status": False})
                print("✅ Firebase Updated: Ready=stop, Status=False")

            threading.Thread(target=delayed_stop, daemon=True).start()

            # ✅ Save to Database
            WasteDisposalRecord.objects.create(
                user=request.user, barcode_id=detected_barcode, barcode_image=barcode_image
            )

        else:
            print("❌ No barcode detected!")

    return redirect('home')
