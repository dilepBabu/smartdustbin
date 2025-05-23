from django.shortcuts import render, redirect,get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WasteBin, WasteDisposal, UserProfile, Redemption
from django.contrib.auth import authenticate, login, logout,authenticate, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone  
from django.db import models  
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
import cv2
from wasteapp.models import RedeemHistory
from django.db.models import Sum
from django.contrib import messages
from django.shortcuts import render, redirect
from wasteapp.models import UserProfile, WasteDisposal, RedeemHistory

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
        barcode_value = request.POST.get('barcode', '')  

        if form.is_valid():
            try:
               
                user_profile = UserProfile.objects.get(barcode_id=barcode_value)

               
                waste_disposal = form.save(commit=False)
                waste_disposal.user = user_profile.user  
                waste_disposal.barcode_id = barcode_value
                waste_disposal.credits_earned = 5
                waste_disposal.timestamp = timezone.now()
                waste_disposal.save()

               
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
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import UserProfile, WasteDisposal, Redemption





@login_required
def dashboard(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)

       
        disposal_history = WasteDisposal.objects.filter(user=request.user).order_by('-timestamp')[:10]
        redemption_history = RedeemHistory.objects.filter(user=request.user).order_by('-timestamp')

        
        total_credits = WasteDisposal.objects.filter(user=request.user).aggregate(
            total=Sum('credits_earned')
        )['total'] or 0  

        
        ranking = UserProfile.objects.annotate(
            computed_credits=Sum('user__wastedisposal__credits_earned')
        ).order_by('-computed_credits')

        
        user_rank = None
        for index, profile in enumerate(ranking, start=1):
            if profile.user == request.user:
                user_rank = index
                break  

        context = {
            'username': request.user.username,
            'barcode_id': user_profile.barcode_id,
            'total_credits': total_credits,
            'disposal_history': disposal_history, 
            'redemption_history': redemption_history, 
            'ranking': ranking,
            'user_rank': user_rank, 
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

        
        backend = get_backends()[0]  
        user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
        
        login(request, user) 

        messages.success(request, "Registration successful!")
        return redirect('dashboard')

    return render(request, 'wasteapp/register.html')

@login_required
def record_waste(request):
    if request.method == 'POST':
        form = WasteDisposalForm(request.POST, request.FILES)
        barcode_value = request.POST.get('barcode', '')  

        if form.is_valid():
            try:
                
                user_profile = UserProfile.objects.get(barcode_id=barcode_value)

                
                waste_disposal = form.save(commit=False)
                waste_disposal.user = user_profile.user  
                waste_disposal.barcode_id = barcode_value
                waste_disposal.credits_earned = 5
                waste_disposal.timestamp = timezone.now()
                waste_disposal.save()

                
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



def extract_barcode_from_image(image):
    img = Image.open(image)
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY) 
    barcodes = decode(img)

    if barcodes:
        return barcodes[0].data.decode('utf-8')  
    return None 

from .forms import RedeemForm


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from wasteapp.models import UserProfile, RedeemHistory
from wasteapp.forms import RedeemForm

def redeem_credits(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == 'POST':
        form = RedeemForm(request.POST)
        if form.is_valid():
            selected_reward = form.cleaned_data['reward']
            required_credits = 70 if selected_reward == 'Sick Leave' else 50

            if user_profile.credits >= required_credits:
                user_profile.credits -= required_credits
                user_profile.save()
                RedeemHistory.objects.create(user=request.user, credits_used=required_credits, reward=selected_reward)
                messages.success(request, f"You have successfully redeemed {selected_reward}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Not enough credits to redeem this reward.")
    else:
        form = RedeemForm()

    return render(request, 'wasteapp/redeem.html', {'form': form, 'credits': user_profile.credits})

from wasteapp.models import WasteDisposal

@login_required
def edit_waste(request, waste_id):
    waste_record = get_object_or_404(WasteDisposal, id=waste_id, user=request.user)

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
    waste_record = get_object_or_404(WasteDisposal, id=waste_id, user=request.user)
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
    waste_records = WasteDisposal.objects.all()

    
    search_query = request.GET.get('search', '')
    waste_type_filter = request.GET.get('waste_type', '')
    start_date = parse_date(request.GET.get('start_date', ''))
    end_date = parse_date(request.GET.get('end_date', ''))

   
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

   
    waste_types = WasteDisposal.objects.values_list('waste_type', flat=True).distinct()

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
        barcode = request.POST.get("barcode")  

        if barcode:
            ref = db.reference("waste_status")  
            ref.update({
                "ready": "start",  
                "status": True 
            })
            return JsonResponse({"message": "Waste disposal started", "status": "success"})

    return JsonResponse({"message": "No barcode provided", "status": "error"})



from django.shortcuts import render
from django.contrib.auth.models import User
from .models import UserProfile 

def user_ranking(request):
    
    ranking = UserProfile.objects.filter(
        user__is_staff=False,  
        user__is_superuser=False
    ).order_by('-credits') 

    return render(request, 'wasteapp/ranking.html', {'ranking': ranking})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import WasteDisposal  


@login_required
def upload_waste(request):
    """📌 Handle New Waste Upload"""
    if request.method == "POST":
        barcode_image = request.FILES.get('barcode_image')

        if barcode_image:
            waste_entry = WasteDisposal.objects.create(
                user=request.user,
                barcode_image=barcode_image,
                waste_type=request.POST.get('waste_type', 'unknown'),
                ir_sensor=True  
            )
            waste_entry.save()
            return redirect('waste_success')  

    return render(request, "upload_waste.html")
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import WasteDisposal 

import firebase_admin
from firebase_admin import credentials, db
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

def upload_barcode(request):
    """🔥 Upload Barcode & Detect It"""
    if request.method == 'POST' and request.FILES.get('barcode_image'):
        barcode_image = request.FILES['barcode_image']

        
        file_path = default_storage.save('temp/' + barcode_image.name, ContentFile(barcode_image.read()))
        full_path = default_storage.path(file_path)

       
        detected_barcode = detect_barcode(full_path)

        if detected_barcode:
            print(f" Barcode Detected: {detected_barcode}")

            
            ref.update({"Ready": "start", "Status": True})
            print(" Firebase Updated: Ready=start, Status=True")

           
            import threading
            def delayed_stop():
                import time
                time.sleep(15)
                print("⏳ 15s completed. Stopping...")
                ref.update({"Ready": "stop", "Status": False})
                print("✅ Firebase Updated: Ready=stop, Status=False")

            threading.Thread(target=delayed_stop, daemon=True).start()

            # ✅ Save to Database
            WasteDisposal.objects.create(
                user=request.user, barcode_id=detected_barcode, barcode_image=barcode_image
            )

        else:
            print("❌ No barcode detected!")

    return redirect('home')


from django.shortcuts import render
from django.db import connection

def credit_ranking(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT student_id, name, credits, 
                   RANK() OVER (ORDER BY credits DESC) AS ranking_position
            FROM student_credits
        """)
        students = cursor.fetchall()  


    return render(request, 'dashboard.html', {'students': students})

from django.shortcuts import render
from django.db.models import Sum, F
from .models import User, WasteDisposal, Redemption

from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Sum
from .models import WasteDisposal, Redemption

def user_dashboard(request):
    user = request.user 
    barcode_id = getattr(user, 'barcode_id', None)  
    

    total_credits = WasteDisposal.objects.filter(user=user).aggregate(total=Sum('credits_earned'))['total'] or 0
    

    users = User.objects.annotate(
        total_credits=Sum('wastedisposal__credits_earned', default=0)
    ).order_by('-total_credits', 'username')  # Sort by credits, then by name
    

    leaderboard = [
        {'rank': index + 1, 'name': u.username, 'credits': u.total_credits or 0}
        for index, u in enumerate(users)
    ]
    
 
    user_rank = next((item['rank'] for item in leaderboard if item['name'] == user.username), None)
    
 
    disposal_history = WasteDisposal.objects.filter(user=user).order_by('-timestamp').select_related('user')
    redemption_history = Redemption.objects.filter(user=user).order_by('-timestamp')
    
    return render(request, 'dashboard.html', {
        'username': user.username,
        'barcode_id': barcode_id,
        'total_credits': total_credits,
        'user_rank': user_rank,
        'leaderboard': leaderboard[:10], 
        'disposal_history': disposal_history,
        'redemption_history': redemption_history
    })
from django.shortcuts import render
from .models import Redemption

def redemption_history(request):
    redemptions = Redemption.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'wasteapp/redemption_history.html', {'redemptions': redemptions})
from django.shortcuts import render
from .models import WasteDisposal
from django.shortcuts import render
from .models import WasteDisposal

def waste_disposal_history(request):
    waste_history = WasteDisposal.objects.filter(user=request.user).order_by('-timestamp')[:8]
    
    
    print("Waste Disposal History:", waste_history)  
    
    return render(request, 'wasteapp/waste_disposal_history.html', {'waste_history': waste_history})
