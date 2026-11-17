from django.contrib.auth.models import User
from django.test import TestCase

from .models import Hospital, Patient, Referral, UserProfile


class HospitalReferralSystemTests(TestCase):
    def setUp(self):
        self.hospital = Hospital.objects.create(name="Barangay Health Center", level="Level A", address="Batangas", bed_available=10, bed_total=20)
        self.user = User.objects.create_user(username="tester", password="testpass123")
        self.profile = UserProfile.objects.create(user=self.user, role="Admin")
        self.patient = Patient.objects.create(patient_id="TEST001", full_name="Test Patient", age=25, sex="Female", address="Batangas", emergency_contact="09170000000")

    def test_django_auth_login(self):
        logged_in = self.client.login(username="tester", password="testpass123")
        self.assertTrue(logged_in)

    def test_patient_model_created(self):
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(self.patient.full_name, "Test Patient")

    def test_referral_model_created(self):
        Referral.objects.create(patient=self.patient, target_hospital=self.hospital, reason="Consultation", urgency="Routine")
        self.assertEqual(Referral.objects.count(), 1)

    def test_bed_capacity_update(self):
        self.hospital.update_bed_count(12, 22)
        self.assertEqual(self.hospital.bed_available, 12)
        self.assertEqual(self.hospital.bed_total, 22)
