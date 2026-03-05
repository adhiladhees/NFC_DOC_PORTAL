from django.db import models
from django.contrib.auth.models import User


class Patient(models.Model):
	nfc_uid = models.CharField(max_length=100, unique=True)
	name = models.CharField(max_length=200)
	age = models.IntegerField()
	gender = models.CharField(max_length=20)
	blood_group = models.CharField(max_length=5)
	phone = models.CharField(max_length=15)
	address = models.TextField()
	height = models.CharField(max_length=10, blank=True)
	weight = models.CharField(max_length=10, blank=True)
	health_score = models.IntegerField(default=70)

	def __str__(self):
		return self.name


class Vitals(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vitals')
	blood_pressure = models.CharField(max_length=20, blank=True)
	blood_sugar = models.CharField(max_length=20, blank=True)
	heart_rate = models.CharField(max_length=20, blank=True)
	temperature = models.CharField(max_length=10, blank=True)
	spo2 = models.CharField(max_length=10, blank=True)
	weight = models.CharField(max_length=10, blank=True)
	recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	recorded_at = models.DateTimeField(auto_now_add=True)


class LabResult(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_results')
	test_name = models.CharField(max_length=200)
	result = models.CharField(max_length=100)
	reference_range = models.CharField(max_length=100, blank=True)
	status = models.CharField(max_length=20, choices=[('Normal', 'Normal'), ('High', 'High'), ('Low', 'Low'), ('Critical', 'Critical')])
	notes = models.TextField(blank=True)
	file = models.FileField(upload_to='labs/', blank=True, null=True)
	added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	added_at = models.DateTimeField(auto_now_add=True)


class ImagingReport(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='imaging')
	scan_type = models.CharField(max_length=50, choices=[('X-Ray', 'X-Ray'), ('MRI', 'MRI'), ('CT Scan', 'CT Scan'), ('Ultrasound', 'Ultrasound'), ('Echo', 'Echo')])
	body_part = models.CharField(max_length=100)
	findings = models.TextField(blank=True)
	impression = models.TextField(blank=True)
	file = models.FileField(upload_to='imaging/', blank=True, null=True)
	added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	added_at = models.DateTimeField(auto_now_add=True)


class Prescription(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
	medicine = models.CharField(max_length=200)
	dosage = models.CharField(max_length=100)
	duration = models.CharField(max_length=100)
	instructions = models.TextField(blank=True)
	file = models.FileField(upload_to='prescriptions/', blank=True, null=True)
	added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	added_at = models.DateTimeField(auto_now_add=True)


class Surgery(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='surgeries')
	procedure = models.CharField(max_length=200)
	surgery_date = models.DateField()
	surgeon = models.CharField(max_length=200)
	outcome = models.CharField(max_length=50, choices=[('Successful', 'Successful'), ('Complicated', 'Complicated'), ('Ongoing Recovery', 'Ongoing Recovery')])
	notes = models.TextField(blank=True)
	file = models.FileField(upload_to='surgery/', blank=True, null=True)
	added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	added_at = models.DateTimeField(auto_now_add=True)


class Diagnosis(models.Model):
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='diagnoses')
	condition = models.CharField(max_length=200)
	severity = models.CharField(max_length=20, choices=[('Mild', 'Mild'), ('Moderate', 'Moderate'), ('Severe', 'Severe'), ('Chronic', 'Chronic')])
	notes = models.TextField(blank=True)
	added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	added_at = models.DateTimeField(auto_now_add=True)
