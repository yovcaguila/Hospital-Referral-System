import secrets

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Hospital, Patient, Referral, UserProfile


def seed_data():
    hospital_a, _ = Hospital.objects.get_or_create(
        level="Level A",
        defaults={"name": "Barangay Health Center", "address": "Sample St, Batangas", "bed_available": 15, "bed_total": 20},
    )
    hospital_b, _ = Hospital.objects.get_or_create(
        level="Level B",
        defaults={"name": "District Hospital", "address": "District Rd, Batangas", "bed_available": 30, "bed_total": 80},
    )
    hospital_c, _ = Hospital.objects.get_or_create(
        level="Level C",
        defaults={"name": "Batangas Medical Center", "address": "Batangas City", "bed_available": 50, "bed_total": 200},
    )

    default_users = [
        ("admin", "admin123", "Admin", None),
        ("barangay", "barangay123", "Barangay Health Center", hospital_a),
        ("district", "district123", "District Hospital", hospital_b),
        ("batmc", "batmc123", "Batangas Medical Center", hospital_c),
    ]
    for username, password, role, hospital in default_users:
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
        UserProfile.objects.get_or_create(user=user, defaults={"role": role, "hospital": hospital})


def login_view(request):
    seed_data()
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        selected_type = request.POST.get("user_type")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            role_map = {
                "admin": "Admin",
                "barangay": "Barangay Health Center",
                "district": "District Hospital",
                "batmc": "Batangas Medical Center",
            }
            expected_role = role_map.get(selected_type)
            
            try:
                if user.userprofile.role == expected_role:
                    login(request, user)
                    return redirect("dashboard")
                else:
                    messages.error(request, "Role mismatch. Please select your correct assigned user type.")
            except UserProfile.DoesNotExist:
                if user.is_superuser and selected_type == "admin":
                    login(request, user)
                    return redirect("dashboard")
                messages.error(request, "No system profile assigned to this user.")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "login.html")


def signup_view(request):
    seed_data()
    role_map = {
        "admin": ("Admin", None),
        "barangay": ("Barangay Health Center", "Level A"),
        "district": ("District Hospital", "Level B"),
        "batmc": ("Batangas Medical Center", "Level C"),
    }
    if request.method == "POST":
        selected = role_map.get(request.POST.get("user_type"))
        username = request.POST.get("username")
        password = request.POST.get("password")
        if not selected or not username or not password:
            messages.error(request, "Please complete all fields.")
            return redirect("login")
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("login")
        user = User.objects.create_user(username=username, password=password)
        hospital = Hospital.objects.filter(level=selected[1]).first() if selected[1] else None
        UserProfile.objects.create(user=user, role=selected[0], hospital=hospital)
        messages.success(request, "Account created. You can now login.")
    return redirect("login")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    seed_data()
    profile = get_object_or_404(UserProfile, user=request.user)
    hospitals = Hospital.objects.order_by("level")
    manageable_hospitals = hospitals
    
    referrals = Referral.objects.select_related("patient", "origin_hospital", "target_hospital").order_by("created_at")
    patients = Patient.objects.order_by("-created_at")
    
    if profile.hospital:
        receiving_hospitals = Hospital.objects.exclude(id=profile.hospital.id).order_by("level")
    else:
        receiving_hospitals = Hospital.objects.order_by("level")
    
    # Inside the dashboard(request) function:
    if profile.hospital:
        referrals = referrals.filter(
            Q(origin_hospital=profile.hospital) | Q(target_hospital=profile.hospital)
        )
        
        # NEW FIX: Only show patients assigned here, coming from here, or sent here
        patients = Patient.objects.filter(
            Q(hospital=profile.hospital) | 
            Q(referrals__target_hospital=profile.hospital) | 
            Q(referrals__origin_hospital=profile.hospital)
        ).distinct().order_by("-created_at")
        
        manageable_hospitals = hospitals.filter(id=profile.hospital.id)
        hospitals = hospitals.filter(id=profile.hospital.id)
    
    if profile.hospital:
        pending_count = referrals.filter(status="Pending", target_hospital=profile.hospital).count()
    else:
        pending_count = referrals.filter(status="Pending").count()
        
    priority_referrals = referrals.filter(urgency__in=["Urgent", "Emergency"]).exclude(status="Completed")
    
    if profile.role == "Admin":
        hospital_a_referrals = Referral.objects.filter(target_hospital__level="Level A")
        hospital_b_referrals = Referral.objects.filter(target_hospital__level="Level B")
        hospital_c_referrals = Referral.objects.filter(target_hospital__level="Level C")
    else:
        hospital_a_referrals = referrals.filter(target_hospital__level="Level A")
        hospital_b_referrals = referrals.filter(target_hospital__level="Level B")
        hospital_c_referrals = referrals.filter(target_hospital__level="Level C")
    
    context = {
        "profile": profile,
        "patients": patients,
        "hospitals": hospitals,
        "receiving_hospitals": receiving_hospitals,
        "manageable_hospitals": manageable_hospitals,
        "referrals": referrals,
        "pending_count": pending_count,
        "priority_referrals": priority_referrals,
        "is_admin": profile.role == "Admin",
        "assigned_hospital": profile.hospital,
        "hospital_a_referrals": hospital_a_referrals,
        "hospital_b_referrals": hospital_b_referrals,
        "hospital_c_referrals": hospital_c_referrals,
        "page_messages": list(messages.get_messages(request)),
    }
    return render(request, "dashboard.html", context)


@login_required
def add_patient(request):
    if request.method == "POST":
        profile = get_object_or_404(UserProfile, user=request.user) # Pull current user profile
        Patient.objects.create(
            patient_id=secrets.token_hex(6).upper(),
            hospital=profile.hospital,  # Attach patient to this facility
            full_name=request.POST.get("name"),
            age=int(request.POST.get("age")),
            sex=request.POST.get("sex"),
            address=request.POST.get("address"),
            emergency_contact=request.POST.get("emergency"),
            allergies=request.POST.get("allergies") or "None recorded",
            chronic_conditions=request.POST.get("chronic") or "None recorded",
            previous_surgeries=request.POST.get("surgeries") or "None recorded",
        )
        messages.success(request, "Patient registered successfully.")
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=patients'))


@login_required
def delete_patient(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    if patient.referrals.exists():
        messages.error(request, "This patient has referral records and cannot be removed yet.")
    else:
        patient.delete()
        messages.success(request, "Patient removed successfully.")
    # FIX: Return directly to the active session URL context
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def patient_profile(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    profile = get_object_or_404(UserProfile, user=request.user)
    
    # FIX: Compute matching excluded hospital structures for the view instance modal 
    if profile.hospital:
        receiving_hospitals = Hospital.objects.exclude(id=profile.hospital.id).order_by("level")
    else:
        receiving_hospitals = Hospital.objects.order_by("level")
        
    referral_history = patient.referrals.order_by("-created_at")
    context = {
        "patient": patient,
        "profile": profile,  # FIX: Attached user profile metadata context to render sidebars safely
        "receiving_hospitals": receiving_hospitals, # FIX: Excluded self from options
        "referral_history": referral_history,
    }
    return render(request, "patient_profile.html", context)


@login_required
def add_referral(request):
    if request.method == "POST":
        patient = get_object_or_404(Patient, id=request.POST.get("patient_id"))
        hospital = get_object_or_404(Hospital, id=request.POST.get("hospital_id"))
        profile = get_object_or_404(UserProfile, user=request.user)
        
        pathway = "Level A care for barangay health services"
        if hospital.level == "Level B":
            pathway = "Level B care for district hospital stabilization"
        if hospital.level == "Level C":
            pathway = "Level C care for advanced medical center services"
            
        Referral.objects.create(
            patient=patient,
            origin_hospital=profile.hospital,
            target_hospital=hospital,
            reason=request.POST.get("reason"),
            urgency=request.POST.get("urgency"),
            notes=request.POST.get("notes") or "No notes provided.",
            pathway=pathway,
        )
        messages.success(request, "Referral created successfully.")
    # FIX: Dynamic redirection to stay directly on active workspace layer
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=referrals'))


@login_required
def accept_referral(request, referral_id):
    referral = get_object_or_404(Referral, id=referral_id)
    profile = get_object_or_404(UserProfile, user=request.user)
    if profile.role != "Admin" and profile.hospital and referral.target_hospital != profile.hospital:
        messages.error(request, "You can only accept referrals for your assigned hospital.")
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=referrals'))
    
    if referral.status == "Accepted":
        messages.info(request, "This referral has already been accepted.")
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=referrals'))
        
    hospital = referral.target_hospital
    if hospital.bed_available <= 0:
        messages.error(request, f"Cannot accept referral. {hospital.name} has no available beds remaining.")
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=referrals'))

    referral.status = "Accepted"
    referral.updated_at = timezone.now()
    referral.save()
    
    hospital.bed_available -= 1
    hospital.save()
    
    messages.success(request, f"Referral accepted successfully. Bed allocated at {hospital.name}.")
    # FIX: Keeps user on active workspace
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=referrals'))


@login_required
def complete_referral(request, referral_id):
    referral = get_object_or_404(Referral, id=referral_id)
    profile = get_object_or_404(UserProfile, user=request.user)
    if profile.role != "Admin" and profile.hospital and referral.target_hospital != profile.hospital:
        messages.error(request, "You can only complete referrals for your assigned hospital.")
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=referrals'))
    
    old_status = referral.status
    referral.status = "Completed"
    referral.updated_at = timezone.now()
    referral.save()
    
    if old_status == "Accepted":
        hospital = referral.target_hospital
        if hospital.bed_available < hospital.bed_total:
            hospital.bed_available += 1
            hospital.save()
            
    messages.success(request, "Referral marked as completed.")
    # FIX: Keeps user on active workspace
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=history'))


@login_required
def remove_referral(request, referral_id):
    referral = get_object_or_404(Referral, id=referral_id)
    
    old_status = referral.status
    referral.status = "Removed"
    referral.updated_at = timezone.now()
    referral.save()
    
    if old_status == "Accepted":
        hospital = referral.target_hospital
        if hospital.bed_available < hospital.bed_total:
            hospital.bed_available += 1
            hospital.save()
            
    messages.success(request, "Referral moved to history as removed.")
    # FIX: Keeps user on active workspace
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=history'))


@login_required
def delete_referral(request, referral_id):
    referral = get_object_or_404(Referral, id=referral_id)
    referral.delete()
    # FIX: Keeps user on active workspace
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=history'))


@login_required
def update_beds(request, hospital_id):
    hospital = get_object_or_404(Hospital, id=hospital_id)
    profile = get_object_or_404(UserProfile, user=request.user)
    
    if profile.role != "Admin" and profile.hospital and profile.hospital != hospital:
        messages.error(request, "You can only update your assigned hospital.")
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=beds'))
        
    if request.method == "POST":
        new_available = int(request.POST.get("available"))
        new_total = int(request.POST.get("total"))
        
        # --- NEW DYNAMIC SYNC LOGIC ---
        
        # 1. Prevent completely illogical manual entries
        if new_available > new_total:
            messages.error(request, "Update failed: Available beds cannot be greater than Total beds.")
            return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=beds'))
            
        # 2. Calculate the exact number of beds currently locked by accepted referrals
        active_referrals_count = Referral.objects.filter(target_hospital=hospital, status="Accepted").count()
        
        # 3. Prevent the hospital from setting their Total Beds lower than their active system patients
        if new_total < active_referrals_count:
            messages.error(request, f"Update failed: You currently have {active_referrals_count} active patients from the referral system. Your Total Beds cannot be lower than this number.")
            return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=beds'))
            
        # 4. Prevent the hospital from declaring available beds that ignore their active system patients
        max_allowed_available = new_total - active_referrals_count
        if new_available > max_allowed_available:
            messages.error(request, f"Update failed: With {new_total} Total Beds and {active_referrals_count} active system referrals, your Available Beds cannot exceed {max_allowed_available}.")
            return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=beds'))
            
        # ------------------------------
        
        # If all mathematical limits are respected, process the update
        hospital.update_bed_count(new_available, new_total)
        hospital.name = request.POST.get("name", hospital.name)
        hospital.address = request.POST.get("address", hospital.address)
        hospital.updated_at = timezone.now()
        hospital.save()
        messages.success(request, "Bed capacity synchronized and updated successfully.")
        
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/?page=beds'))