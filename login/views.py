from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from matplotlib.style import context
import json
from decimal import Decimal, InvalidOperation
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from .models import ActivityLog, Fee, Room
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .models import Floor
from .models import Allocation
from .models import Complaint
from .forms import UserRegisterForm, ComplaintForm

@login_required(login_url='login')
def home(request):
    context = {
        'user': request.user,
        'is_authenticated': request.user.is_authenticated,
    }
    return render(request, 'home.html', context)

def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect('home')
        else:
            messages.error(request, "Failed to register. Please check the credentials.")
            return render(request, 'register.html', {'form': form})
    else:
        form = UserRegisterForm()
        return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')

@login_required(login_url='login')
def complaint_view(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.name = request.user.username
            complaint.email = request.user.email
            complaint.save()
            messages.success(request, "Complaint submitted successfully.")
            return redirect('home')
        else:
            complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')
            return render(request, 'complaint.html', {'form': form, 'complaints': complaints, 'user': request.user})
    else:
        form = ComplaintForm()
    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'complaint.html', {'form': form, 'complaints': complaints, 'user': request.user})

@login_required(login_url='login')
def fee_view(request):
    FIXED_TOTAL_FEE = 200000  # Set your fixed amount here
    # Get or create the fee record for the user
    fee_record, created = Fee.objects.get_or_create(
        user=request.user, 
        defaults={'amount': FIXED_TOTAL_FEE, 'paid': False}
    )
    if request.method == 'POST':
        payment_input = request.POST.get('fee_amount')
        
        try:
            payment_amount = Decimal(payment_input)
            
            if payment_amount <= 0:
                messages.error(request, "Please enter a valid amount.")
            elif payment_amount > fee_record.amount:
                # If user enters more than owed, settle the fee fully and avoid confusion about exact overpay numbers.
                fee_record.amount = 0
                fee_record.paid = True
                fee_record.save()
                messages.success(request, "Payment successful. Your remaining balance is now 0.")
                return redirect('fee')
            else:
                # Subtract the payment from the remaining balance
                fee_record.amount -= payment_amount
                # If balance hits zero, mark as paid
                if fee_record.amount <= 0:
                    fee_record.amount = 0
                    fee_record.paid = True
                fee_record.save()
                messages.success(request, f"Payment of {payment_amount} successful!")
                return redirect('fee')
                
        except (InvalidOperation, ValueError, TypeError):
            messages.error(request, "Invalid payment amount entered.")

    paid_amount = FIXED_TOTAL_FEE - fee_record.amount
    if paid_amount < 0:
        paid_amount = 0

    return render(request, 'fee.html', {
        'user': request.user,
        'remaining_balance': fee_record.amount,
        'is_paid': fee_record.paid,
        'total_fee': FIXED_TOTAL_FEE,
        'fee': fee_record,
        'paid_amount': paid_amount,
    })

@login_required
def room_allocation(request):
    """Main room allocation page."""

    # Get all floors for the dropdown
    floors = Floor.objects.all().order_by('number')

    # Determine current floor (from GET param or first floor)
    floor_id = request.GET.get('floor')
    if floor_id:
        current_floor = get_object_or_404(Floor, id=floor_id)
    else:
        current_floor = floors.first()

    # Fetch all rooms on this floor
    rooms = Room.objects.filter(floor=current_floor).order_by('number')

    # Build JSON for frontend
    rooms_json = []
    for room in rooms:
        rooms_json.append({
            "number":           room.number,
            "type":             room.get_room_type_display(),
            "floor":            current_floor.name,
            "current":          room.current_occupancy,
            "capacity":         room.capacity,
            "price":            room.price_per_semester,
            "status":           room.get_status(),      # 'available' | 'occupied' | 'female'
            "amenities":        room.amenities_list(),  # e.g. ['wifi', 'study_table', 'wardrobe']
            "attached_washroom": room.attached_washroom,
            "position":         room.position,          # 'top' | 'bottom' (which row in the floor map)
        })

    context = {
        "floors":        floors,
        "current_floor": current_floor,
        "rooms_json":    json.dumps(rooms_json),
    }
    return render(request, "test_room.html", context)


@login_required
@require_POST
@csrf_protect
def allocate_room(request):
    """Handle room allocation form submission (AJAX)."""
    try:
        body = json.loads(request.body)
        room_number = body.get("room_number")
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"success": False, "error": "Invalid request."}, status=400)

    # Check the student doesn't already have an allocation
    if Allocation.objects.filter(student=request.user).exists():
        return JsonResponse({"success": False, "error": "You already have a room allocated."}, status=400)

    room = get_object_or_404(Room, number=room_number)

    # Validate the room is still available
    if room.get_status() != "available":
        return JsonResponse({"success": False, "error": "Room is no longer available."}, status=400)

    # Create the allocation
    Allocation.objects.create(student=request.user, room=room)

    return JsonResponse({"success": True, "redirect": "/hostel/confirmation/"})


@login_required(login_url='login')
def status_view(request):
    return render(request, 'status.html')

@login_required
def profile_view(request):
    user = request.user
    
    # Fetch the latest 4 activities for this user
    recent_activities = user.activities.all()[:4]

    # Handle Password Change form submission
    if request.method == 'POST':
        password_form = PasswordChangeForm(user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            # Updating the password logs the user out by default. This keeps them logged in.
            update_session_auth_hash(request, user)
            
            # Log the activity
            ActivityLog.objects.create(user=user, action="Password updated successfully")
            
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        password_form = PasswordChangeForm(user)

    context = {
        'password_form': password_form,
        'recent_activities': recent_activities,
        'user': request.user,
    }
    
    return render(request, 'profile.html', context)

