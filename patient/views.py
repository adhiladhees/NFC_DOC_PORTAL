from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *


@login_required
def search_patient(request):
	error = None
	if request.method == 'POST':
		uid = request.POST.get('nfc_uid', '').strip()
		if not uid:
			return render(request, 'patient/search.html', {'error': 'Please enter a patient NFC UID.'})
		try:
			patient = Patient.objects.get(nfc_uid=uid)
			return redirect('patient_detail', patient_id=patient.id)
		except Patient.DoesNotExist:
			error = 'No patient found with this NFC ID'
	return render(request, 'patient/search.html', {'error': error})


@login_required
def patient_detail(request, patient_id):
	patient = get_object_or_404(Patient, id=patient_id)
	vitals = patient.vitals.order_by('-recorded_at')
	labs = patient.lab_results.order_by('-added_at')
	imaging = patient.imaging.order_by('-added_at')
	prescriptions = patient.prescriptions.order_by('-added_at')
	surgeries = patient.surgeries.order_by('-added_at')
	diagnoses = patient.diagnoses.order_by('-added_at')

	visit_log = []
	for item in vitals:
		visit_log.append({
			'timestamp': item.recorded_at,
			'doctor': item.recorded_by.get_full_name() if item.recorded_by else 'Unknown',
			'action': 'added Vitals',
			'summary': f"BP {item.blood_pressure or '-'}, Sugar {item.blood_sugar or '-'}, HR {item.heart_rate or '-'}"
		})
	for item in labs:
		visit_log.append({
			'timestamp': item.added_at,
			'doctor': item.added_by.get_full_name() if item.added_by else 'Unknown',
			'action': 'added Lab Result',
			'summary': f"{item.test_name} [{item.status}]"
		})
	for item in imaging:
		visit_log.append({
			'timestamp': item.added_at,
			'doctor': item.added_by.get_full_name() if item.added_by else 'Unknown',
			'action': 'added Imaging',
			'summary': f"{item.scan_type} - {item.body_part}"
		})
	for item in prescriptions:
		visit_log.append({
			'timestamp': item.added_at,
			'doctor': item.added_by.get_full_name() if item.added_by else 'Unknown',
			'action': 'added Prescription',
			'summary': item.medicine
		})
	for item in surgeries:
		visit_log.append({
			'timestamp': item.added_at,
			'doctor': item.added_by.get_full_name() if item.added_by else 'Unknown',
			'action': 'added Surgery',
			'summary': f"{item.procedure} [{item.outcome}]"
		})
	for item in diagnoses:
		visit_log.append({
			'timestamp': item.added_at,
			'doctor': item.added_by.get_full_name() if item.added_by else 'Unknown',
			'action': 'added Diagnosis',
			'summary': f"{item.condition} [{item.severity}]"
		})

	visit_log = sorted(visit_log, key=lambda entry: entry['timestamp'], reverse=True)

	context = {
		'patient': patient,
		'vitals': vitals,
		'labs': labs,
		'imaging': imaging,
		'prescriptions': prescriptions,
		'surgeries': surgeries,
		'diagnoses': diagnoses,
		'visit_log': visit_log[:20],
	}
	return render(request, 'patient/detail.html', context)


@login_required
def add_vitals(request, patient_id):
	patient = get_object_or_404(Patient, id=patient_id)
	if request.method == 'POST':
		blood_pressure = request.POST.get('blood_pressure', '').strip()
		blood_sugar = request.POST.get('blood_sugar', '').strip()
		heart_rate = request.POST.get('heart_rate', '').strip()
		temperature = request.POST.get('temperature', '').strip()
		spo2 = request.POST.get('spo2', '').strip()
		weight = request.POST.get('weight', '').strip()

		if not all([blood_pressure, blood_sugar, heart_rate, temperature, spo2, weight]):
			messages.error(request, 'All vitals fields are required.')
			return redirect('patient_detail', patient_id=patient_id)

		Vitals.objects.create(
			patient=patient,
			blood_pressure=blood_pressure,
			blood_sugar=blood_sugar,
			heart_rate=heart_rate,
			temperature=temperature,
			spo2=spo2,
			weight=weight,
			recorded_by=request.user
		)
		messages.success(request, 'Vitals saved successfully.')
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_vitals(request, patient_id, vitals_id):
	patient = get_object_or_404(Patient, id=patient_id)
	vitals_record = get_object_or_404(Vitals, id=vitals_id, patient=patient)
	if request.method == 'POST':
		vitals_record.delete()
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def add_lab(request, patient_id):
	patient = get_object_or_404(Patient, id=patient_id)
	if request.method == 'POST':
		LabResult.objects.create(
			patient=patient,
			test_name=request.POST['test_name'],
			result=request.POST['result'],
			reference_range=request.POST.get('reference_range', ''),
			status=request.POST['status'],
			notes=request.POST.get('notes', ''),
			file=request.FILES.get('file'),
			added_by=request.user
		)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_lab(request, patient_id, lab_id):
	patient = get_object_or_404(Patient, id=patient_id)
	lab_record = get_object_or_404(LabResult, id=lab_id, patient=patient)
	if request.method == 'POST':
		if lab_record.file:
			lab_record.file.delete(save=False)
		lab_record.delete()
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def add_imaging(request, patient_id):
	patient = get_object_or_404(Patient, id=patient_id)
	if request.method == 'POST':
		ImagingReport.objects.create(
			patient=patient,
			scan_type=request.POST['scan_type'],
			body_part=request.POST['body_part'],
			findings=request.POST.get('findings', ''),
			impression=request.POST.get('impression', ''),
			file=request.FILES.get('file'),
			added_by=request.user
		)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_imaging(request, patient_id, imaging_id):
	patient = get_object_or_404(Patient, id=patient_id)
	imaging_record = get_object_or_404(ImagingReport, id=imaging_id, patient=patient)
	if request.method == 'POST':
		if imaging_record.file:
			imaging_record.file.delete(save=False)
		imaging_record.delete()
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def add_prescription(request, patient_id):
	patient = get_object_or_404(Patient, id=patient_id)
	if request.method == 'POST':
		Prescription.objects.create(
			patient=patient,
			medicine=request.POST['medicine'],
			dosage=request.POST['dosage'],
			duration=request.POST['duration'],
			instructions=request.POST.get('instructions', ''),
			file=request.FILES.get('file'),
			added_by=request.user
		)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_prescription(request, patient_id, prescription_id):
	patient = get_object_or_404(Patient, id=patient_id)
	prescription_record = get_object_or_404(Prescription, id=prescription_id, patient=patient)
	if request.method == 'POST':
		if prescription_record.file:
			prescription_record.file.delete(save=False)
		prescription_record.delete()
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def add_surgery(request, patient_id):
	patient = get_object_or_404(Patient, id=patient_id)
	if request.method == 'POST':
		Surgery.objects.create(
			patient=patient,
			procedure=request.POST['procedure'],
			surgery_date=request.POST['surgery_date'],
			surgeon=request.POST['surgeon'],
			outcome=request.POST['outcome'],
			notes=request.POST.get('notes', ''),
			file=request.FILES.get('file'),
			added_by=request.user
		)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_surgery(request, patient_id, surgery_id):
	patient = get_object_or_404(Patient, id=patient_id)
	surgery_record = get_object_or_404(Surgery, id=surgery_id, patient=patient)
	if request.method == 'POST':
		if surgery_record.file:
			surgery_record.file.delete(save=False)
		surgery_record.delete()
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def add_diagnosis(request, patient_id):
	patient = get_object_or_404(Patient, id=patient_id)
	if request.method == 'POST':
		Diagnosis.objects.create(
			patient=patient,
			condition=request.POST['condition'],
			severity=request.POST['severity'],
			notes=request.POST.get('notes', ''),
			added_by=request.user
		)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_diagnosis(request, patient_id, diagnosis_id):
	patient = get_object_or_404(Patient, id=patient_id)
	diagnosis_record = get_object_or_404(Diagnosis, id=diagnosis_id, patient=patient)
	if request.method == 'POST':
		diagnosis_record.delete()
	return redirect('patient_detail', patient_id=patient_id)
