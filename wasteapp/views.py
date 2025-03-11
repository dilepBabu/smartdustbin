from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WasteBin, WasteDisposalRecord, UserProfile  # ✅ Removed 'WasteDisposal'
from django.utils.timezone import now
from django.contrib.auth import authenticate, login, logout,authenticate, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image
from .forms import WasteDisposalForm
@api_view(['GET'])
def get_bins(request):
    bins = WasteBin.objects.all().values()
    return Response({'bins': list(bins)})

@api_view(['POST'])
def record_waste(request):
    barcode = request.data.get('barcode_id')
    bin_id = request.data.get('bin_id')
    weight = float(request.data.get('weight'))

    try:
        user = UserProfile.objects.get(barcode_id=barcode)
        bin = WasteBin.objects.get(bin_id=bin_id)
        credits = int(weight * 5)  # 5 points per kg of waste

        WasteDisposal.objects.create(user=user, bin=bin, weight=weight, timestamp=now(), credits_earned=credits)
        user.credits += credits
        user.save()

        return Response({'message': 'Waste recorded successfully!', 'credits_earned': credits})
    except:
        return Response({'error': 'Invalid barcode or bin ID'}, status=400)
    

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
    user_profile = UserProfile.objects.get(user=request.user)
    disposal_history = WasteDisposalRecord.objects.filter(user=request.user).order_by('-timestamp')  # Fetch history

    context = {
        'username': request.user.username,
        'barcode_id': user_profile.barcode_id,
        'total_credits': user_profile.credits,
        'disposal_history': disposal_history,  # Pass records to template
    }
    return render(request, 'wasteapp/dashboard.html', context)

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
            waste_disposal = form.save(commit=False)
            waste_disposal.user = request.user
            waste_disposal.name = request.user.username

            # If barcode is scanned using live camera
            if barcode_value:
                waste_disposal.barcode_id = barcode_value

            # If barcode image is uploaded, extract barcode
            elif 'barcode_image' in request.FILES:
                image = request.FILES['barcode_image']
                barcode = extract_barcode_from_image(image)
                if barcode:
                    waste_disposal.barcode_id = barcode
                else:
                    messages.error(request, "No barcode detected in the image.")
                    return redirect('record_waste')

            waste_disposal.credits_earned = 5
            waste_disposal.save()

            # Update user credits
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.credits += 5
            user_profile.save()

            messages.success(request, "Waste disposal recorded successfully!")
            return redirect('dashboard')
    else:
        form = WasteDisposalForm()

    return render(request, 'wasteapp/record_waste.html', {'form': form})

# ✅ Function to extract barcode from an uploaded image
def extract_barcode_from_image(image):
    img = Image.open(image)
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)  # Convert to grayscale
    barcodes = decode(img)
    
    if barcodes:
        return barcodes[0].data.decode('utf-8')  # ✅ Return barcode text
    return None