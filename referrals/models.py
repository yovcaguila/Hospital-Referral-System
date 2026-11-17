from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Hospital(models.Model):
    LEVEL_CHOICES = [
        ("Level A", "Hospital A - Barangay Health Center"),
        ("Level B", "Hospital B - District Hospital"),
        ("Level C", "Hospital C - Medical Center"),
    ]

    name = models.CharField(max_length=120)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    address = models.CharField(max_length=255)
    bed_total = models.PositiveIntegerField(default=0)
    bed_available = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(default=timezone.now)

    def update_bed_count(self, available, total):
        self.bed_available = available
        self.bed_total = total
        self.updated_at = timezone.now()
        self.save()

    def get_availability(self):
        if self.bed_total == 0:
            return 0
        return round((self.bed_available / self.bed_total) * 100)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Barangay Health Center", "Barangay Health Center"),
        ("District Hospital", "District Hospital"),
        ("Batangas Medical Center", "Batangas Medical Center"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=80, choices=ROLE_CHOICES)
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)

    def get_role(self):
        return self.role

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Patient(models.Model):
    patient_id = models.CharField(max_length=30, unique=True)
    
    # NEW FIX: Ties the patient permanently to their registering hospital
    hospital = models.ForeignKey(Hospital, related_name="registered_patients", on_delete=models.SET_NULL, null=True, blank=True)
    
    full_name = models.CharField(max_length=120)
    age = models.PositiveIntegerField()
    sex = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    emergency_contact = models.CharField(max_length=40)
    allergies = models.CharField(max_length=255, default="None recorded")
    chronic_conditions = models.CharField(max_length=255, default="None recorded")
    previous_surgeries = models.CharField(max_length=255, default="None recorded")
    status = models.CharField(max_length=50, default="Active")
    created_at = models.DateTimeField(default=timezone.now)

    def register(self):
        self.save()

    def update_profile(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()

    def get_history(self):
        return self.referrals.order_by("-created_at")

    def __str__(self):
        return self.full_name


class Referral(models.Model):
    URGENCY_CHOICES = [
        ("Routine", "Routine"),
        ("Urgent", "Urgent"),
        ("Emergency", "Emergency"),
    ]
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Accepted", "Accepted"),
        ("Completed", "Completed"),
        ("Removed", "Removed"),
    ]

    patient = models.ForeignKey(Patient, related_name="referrals", on_delete=models.CASCADE)
    origin_hospital = models.ForeignKey(Hospital, related_name="origin_referrals", on_delete=models.SET_NULL, null=True, blank=True)
    target_hospital = models.ForeignKey(Hospital, related_name="target_referrals", on_delete=models.CASCADE)
    reason = models.TextField()
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    notes = models.TextField(blank=True, default="No notes provided.")
    pathway = models.CharField(max_length=255, default="Referral pathway pending classification")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def create_referral(self):
        self.save()

    def update_status(self, status):
        self.status = status
        self.updated_at = timezone.now()
        self.save()

    def route_to_facility(self):
        return self.target_hospital

    def get_history(self):
        return f"{self.patient.full_name} - {self.status}"

    def __str__(self):
        return f"{self.patient.full_name} to {self.target_hospital.name}"


class TriageRecord(models.Model):
    patient = models.ForeignKey(Patient, related_name="triage_records", on_delete=models.CASCADE)
    blood_pressure = models.CharField(max_length=30, blank=True)
    heart_rate = models.PositiveIntegerField(default=0)
    respiratory_rate = models.PositiveIntegerField(default=0)
    oxygen_sat = models.PositiveIntegerField(default=0)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, default=36.5)
    severity = models.CharField(max_length=20, default="Routine")
    recorded_at = models.DateTimeField(default=timezone.now)

    def classify_severity(self):
        if self.oxygen_sat and self.oxygen_sat < 92:
            return "Emergency"
        if self.heart_rate and self.heart_rate > 120:
            return "Urgent"
        return "Routine"

    def recommend_facility(self):
        if self.severity == "Emergency":
            return Hospital.objects.filter(level="Level C").first()
        if self.severity == "Urgent":
            return Hospital.objects.filter(level="Level B").first()
        return Hospital.objects.filter(level="Level A").first()

    def save(self, *args, **kwargs):
        self.severity = self.classify_severity()
        super().save(*args, **kwargs)


class MedicalDocument(models.Model):
    referral = models.ForeignKey(Referral, related_name="documents", on_delete=models.CASCADE)
    file_path = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=80)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def upload(self):
        self.save()

    def retrieve(self):
        return self.file_path
