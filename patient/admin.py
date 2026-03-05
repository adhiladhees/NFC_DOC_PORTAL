from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
	list_display = ('id', 'nfc_uid', 'name', 'age', 'gender', 'phone')
	search_fields = ('nfc_uid', 'name', 'phone')
