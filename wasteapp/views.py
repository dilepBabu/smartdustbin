from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WasteBin, WasteDisposal, UserProfile
from django.utils.timezone import now
from django.contrib.auth import authenticate, login, logout,authenticate, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
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

@login_required
def dashboard(request):
    return render(request, 'wasteapp/dashboard.html')

def user_logout(request):
    logout(request)
    return redirect('login')
def dashboard(request):
    return render(request, 'wasteapp/dashboard.html')

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