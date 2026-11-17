from django.contrib import admin
from django.urls import path

from referrals import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("patients/add/", views.add_patient, name="add_patient"),
    path("patients/<int:patient_id>/", views.patient_profile, name="patient_profile"),
    path("patients/<int:patient_id>/delete/", views.delete_patient, name="delete_patient"),
    path("referrals/add/", views.add_referral, name="add_referral"),
    path("referrals/<int:referral_id>/accept/", views.accept_referral, name="accept_referral"),
    path("referrals/<int:referral_id>/complete/", views.complete_referral, name="complete_referral"),
    path("referrals/<int:referral_id>/remove/", views.remove_referral, name="remove_referral"),
    path("referrals/<int:referral_id>/delete/", views.delete_referral, name="delete_referral"),
    path("beds/<int:hospital_id>/update/", views.update_beds, name="update_beds"),
]
