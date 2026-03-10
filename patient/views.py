import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *


def recalculate_health_score(patient):
    score = 100

    # Diagnoses
    for d in patient.diagnoses.all():
        if d.severity == 'Chronic':   score -= 15
        elif d.severity == 'Severe':  score -= 12
        elif d.severity == 'Moderate':score -= 6
        elif d.severity == 'Mild':    score -= 3

    # Lab results
    for l in patient.lab_results.all():
        if l.status == 'Critical':    score -= 10
        elif l.status == 'High':      score -= 5
        elif l.status == 'Low':       score -= 3

    # Latest vitals only
    latest = patient.vitals.order_by('-recorded_at').first()
    if latest:
        try:
            sys_bp = int(latest.blood_pressure.split('/')[0])
            if sys_bp > 140: score -= 5
        except: pass
        try:
            if float(latest.blood_sugar) > 140: score -= 5
        except: pass
        try:
            if float(latest.spo2) < 95: score -= 5
        except: pass
        try:
            hr = float(latest.heart_rate)
            if hr > 100 or hr < 60: score -= 3
        except: pass

    # Surgery
    for s in patient.surgeries.all():
        if s.outcome == 'Complicated':       score -= 8
        elif s.outcome == 'Ongoing Recovery':score -= 5

    patient.health_score = max(0, min(100, score))
    patient.save()


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
	recalculate_health_score(patient)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_vitals(request, patient_id, vitals_id):
	patient = get_object_or_404(Patient, id=patient_id)
	vitals_record = get_object_or_404(Vitals, id=vitals_id, patient=patient)
	if request.method == 'POST':
		vitals_record.delete()
	recalculate_health_score(patient)
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
	recalculate_health_score(patient)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_lab(request, patient_id, lab_id):
	patient = get_object_or_404(Patient, id=patient_id)
	lab_record = get_object_or_404(LabResult, id=lab_id, patient=patient)
	if request.method == 'POST':
		if lab_record.file:
			lab_record.file.delete(save=False)
		lab_record.delete()
	recalculate_health_score(patient)
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
	recalculate_health_score(patient)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_imaging(request, patient_id, imaging_id):
	patient = get_object_or_404(Patient, id=patient_id)
	imaging_record = get_object_or_404(ImagingReport, id=imaging_id, patient=patient)
	if request.method == 'POST':
		if imaging_record.file:
			imaging_record.file.delete(save=False)
		imaging_record.delete()
	recalculate_health_score(patient)
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
	recalculate_health_score(patient)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_prescription(request, patient_id, prescription_id):
	patient = get_object_or_404(Patient, id=patient_id)
	prescription_record = get_object_or_404(Prescription, id=prescription_id, patient=patient)
	if request.method == 'POST':
		if prescription_record.file:
			prescription_record.file.delete(save=False)
		prescription_record.delete()
	recalculate_health_score(patient)
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
	recalculate_health_score(patient)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_surgery(request, patient_id, surgery_id):
	patient = get_object_or_404(Patient, id=patient_id)
	surgery_record = get_object_or_404(Surgery, id=surgery_id, patient=patient)
	if request.method == 'POST':
		if surgery_record.file:
			surgery_record.file.delete(save=False)
		surgery_record.delete()
	recalculate_health_score(patient)
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
	recalculate_health_score(patient)
	return redirect('patient_detail', patient_id=patient_id)


@login_required
def delete_diagnosis(request, patient_id, diagnosis_id):
	patient = get_object_or_404(Patient, id=patient_id)
	diagnosis_record = get_object_or_404(Diagnosis, id=diagnosis_id, patient=patient)
	if request.method == 'POST':
		diagnosis_record.delete()
	recalculate_health_score(patient)
	return redirect('patient_detail', patient_id=patient_id)


# ── API 1: Fetch patient by NFC UID (used by mobile app after card tap) ──
def patient_api(request, nfc_uid):
	try:
		patient = Patient.objects.get(nfc_uid__iexact=nfc_uid)

		import json as json_module
		from django.core.serializers.json import DjangoJSONEncoder

		data = {
			'found': True,
			'id': patient.id,
			'nfc_uid': patient.nfc_uid,
			'name': patient.name,
			'age': patient.age,
			'gender': patient.gender,
			'blood_group': patient.blood_group,
			'phone': patient.phone,
			'address': patient.address,
			'height': patient.height,
			'weight': patient.weight,
			'health_score': patient.health_score,

			'vitals': list(patient.vitals.order_by('-recorded_at').values(
				'id', 'blood_pressure', 'blood_sugar', 'heart_rate',
				'temperature', 'spo2', 'weight', 'recorded_at',
				'recorded_by__username'
			)),
			'lab_results': list(patient.lab_results.order_by('-added_at').values(
				'id', 'test_name', 'result', 'reference_range',
				'status', 'notes', 'added_at', 'added_by__username'
			)),
			'imaging': list(patient.imaging.order_by('-added_at').values(
				'id', 'scan_type', 'body_part', 'findings',
				'impression', 'added_at', 'added_by__username'
			)),
			'prescriptions': list(patient.prescriptions.order_by('-added_at').values(
				'id', 'medicine', 'dosage', 'duration',
				'instructions', 'added_at', 'added_by__username'
			)),
			'surgeries': list(patient.surgeries.order_by('-surgery_date').values(
				'id', 'procedure', 'surgery_date', 'surgeon',
				'outcome', 'notes', 'added_by__username'
			)),
			'diagnoses': list(patient.diagnoses.order_by('-added_at').values(
				'id', 'condition', 'severity', 'notes',
				'added_at', 'added_by__username'
			)),
		}

		data_str = json_module.dumps(data, cls=DjangoJSONEncoder)
		data = json_module.loads(data_str)

	except Patient.DoesNotExist:
		data = {'found': False, 'message': 'No patient found with this NFC ID'}
	return JsonResponse(data)


# ── API 2: Register new patient (used by mobile app on first setup) ──
@csrf_exempt
def patient_register(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            name        = body.get('name', '').strip()
            age         = body.get('age')
            gender      = body.get('gender', '').strip()
            blood_group = body.get('blood_group', '').strip()
            phone       = body.get('phone', '').strip()
            address     = body.get('address', '').strip()
            height      = body.get('height', '').strip()
            weight      = body.get('weight', '').strip()
            pin         = body.get('pin', '0000').strip()

            # Validate required fields
            if not all([name, age, gender, blood_group, phone, address]):
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required'
                }, status=400)

            # Auto generate NFC UID
            count = Patient.objects.count() + 1
            nfc_uid = f'NFC{count:03d}'

            # Make sure UID is unique
            while Patient.objects.filter(nfc_uid=nfc_uid).exists():
                count += 1
                nfc_uid = f'NFC{count:03d}'

            # Create the patient
            patient = Patient.objects.create(
                nfc_uid     = nfc_uid,
                name        = name,
                age         = int(age),
                gender      = gender,
                blood_group = blood_group,
                phone       = phone,
                address     = address,
                height      = height,
                weight      = weight,
                pin         = pin,
                health_score= 100,
            )

            return JsonResponse({
                'success': True,
                'nfc_uid': patient.nfc_uid,
                'name': patient.name,
                'message': 'Patient registered successfully'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'success': False,
        'message': 'Only POST requests allowed'
    }, status=405)


@csrf_exempt
def patient_pin_login(request):
	if request.method == 'POST':
		try:
			body = json.loads(request.body)
			nfc_uid = body.get('nfc_uid', '').strip()
			pin = body.get('pin', '').strip()

			if not nfc_uid or not pin:
				return JsonResponse({
					'success': False,
					'message': 'NFC ID and PIN are required'
				}, status=400)

			patient = Patient.objects.get(nfc_uid__iexact=nfc_uid)

			if patient.pin == pin:
				import json as json_module
				from django.core.serializers.json import DjangoJSONEncoder
				data = {
					'success': True,
					'found': True,
					'id': patient.id,
					'nfc_uid': patient.nfc_uid,
					'name': patient.name,
					'age': patient.age,
					'gender': patient.gender,
					'blood_group': patient.blood_group,
					'phone': patient.phone,
					'address': patient.address,
					'height': patient.height,
					'weight': patient.weight,
					'health_score': patient.health_score,
					'vitals': list(patient.vitals.order_by('-recorded_at').values(
						'id', 'blood_pressure', 'blood_sugar', 'heart_rate',
						'temperature', 'spo2', 'weight', 'recorded_at',
						'recorded_by__username'
					)),
					'lab_results': list(patient.lab_results.order_by('-added_at').values(
						'id', 'test_name', 'result', 'reference_range',
						'status', 'notes', 'added_at', 'added_by__username'
					)),
					'imaging': list(patient.imaging.order_by('-added_at').values(
						'id', 'scan_type', 'body_part', 'findings',
						'impression', 'added_at', 'added_by__username'
					)),
					'prescriptions': list(patient.prescriptions.order_by('-added_at').values(
						'id', 'medicine', 'dosage', 'duration',
						'instructions', 'added_at', 'added_by__username'
					)),
					'surgeries': list(patient.surgeries.order_by('-surgery_date').values(
						'id', 'procedure', 'surgery_date', 'surgeon',
						'outcome', 'notes', 'added_by__username'
					)),
					'diagnoses': list(patient.diagnoses.order_by('-added_at').values(
						'id', 'condition', 'severity', 'notes',
						'added_at', 'added_by__username'
					)),
				}
				data_str = json_module.dumps(data, cls=DjangoJSONEncoder)
				data = json_module.loads(data_str)
				return JsonResponse(data)
			else:
				return JsonResponse({
					'success': False,
					'message': 'Incorrect PIN'
				}, status=401)

		except Patient.DoesNotExist:
			return JsonResponse({
				'success': False,
				'message': 'Patient not found'
			}, status=404)
		except Exception as e:
			return JsonResponse({
				'success': False,
				'message': str(e)
			}, status=500)

	return JsonResponse({
		'success': False,
		'message': 'Only POST requests allowed'
	}, status=405)
