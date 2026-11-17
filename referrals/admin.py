from django.contrib import admin

from .models import Hospital, MedicalDocument, Patient, Referral, TriageRecord, UserProfile

admin.site.register(Hospital)
admin.site.register(UserProfile)
admin.site.register(Patient)
admin.site.register(Referral)
admin.site.register(TriageRecord)
admin.site.register(MedicalDocument)
