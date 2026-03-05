from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from doctor.models import DoctorProfile
from patient.models import Patient, Diagnosis, Vitals


class DoctorPatientFlowTests(TestCase):
	def setUp(self):
		self.patient = Patient.objects.create(
			nfc_uid='NFC001',
			name='Test Patient',
			age=30,
			gender='Male',
			blood_group='O+',
			phone='9999999999',
			address='Test Address'
		)

	def test_signup_creates_doctor_profile_and_logs_in(self):
		response = self.client.post(reverse('signup'), {
			'name': 'John Doe',
			'email': 'john@example.com',
			'specialization': 'Cardiology',
			'hospital': 'City Hospital',
			'password': 'SecurePass123!'
		})

		self.assertRedirects(response, reverse('dashboard'))
		user = User.objects.get(username='john@example.com')
		self.assertTrue(DoctorProfile.objects.filter(user=user).exists())
		self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

	def test_login_search_patient_and_logout_flow(self):
		user = User.objects.create_user(
			username='doc@example.com',
			email='doc@example.com',
			password='SecurePass123!',
			first_name='Doc',
			last_name='Tor'
		)
		DoctorProfile.objects.create(user=user, specialization='General', hospital='UHC')

		login_response = self.client.post(reverse('login'), {
			'email': 'doc@example.com',
			'password': 'SecurePass123!'
		})
		self.assertRedirects(login_response, reverse('dashboard'))

		search_found_response = self.client.post(reverse('search_patient'), {'nfc_uid': 'NFC001'})
		self.assertRedirects(search_found_response, reverse('patient_detail', kwargs={'patient_id': self.patient.id}))

		search_missing_response = self.client.post(reverse('search_patient'), {'nfc_uid': 'NFC404'})
		self.assertContains(search_missing_response, 'No patient found with this NFC ID')

		add_diagnosis_response = self.client.post(
			reverse('add_diagnosis', kwargs={'patient_id': self.patient.id}),
			{
				'condition': 'Hypertension',
				'severity': 'Moderate',
				'notes': 'Monitor weekly'
			}
		)
		self.assertRedirects(add_diagnosis_response, reverse('patient_detail', kwargs={'patient_id': self.patient.id}))

		diagnosis = Diagnosis.objects.get(patient=self.patient)
		self.assertEqual(diagnosis.condition, 'Hypertension')
		self.assertEqual(diagnosis.added_by, user)

		logout_response = self.client.get(reverse('logout'))
		self.assertRedirects(logout_response, reverse('login'))

	def test_delete_vitals_record(self):
		user = User.objects.create_user(
			username='doc2@example.com',
			email='doc2@example.com',
			password='SecurePass123!'
		)
		DoctorProfile.objects.create(user=user, specialization='General', hospital='UHC')

		self.client.post(reverse('login'), {
			'email': 'doc2@example.com',
			'password': 'SecurePass123!'
		})

		vitals = Vitals.objects.create(
			patient=self.patient,
			blood_pressure='120/80',
			blood_sugar='95',
			heart_rate='72',
			temperature='36.6',
			spo2='98',
			weight='70',
			recorded_by=user
		)

		response = self.client.post(
			reverse('delete_vitals', kwargs={'patient_id': self.patient.id, 'vitals_id': vitals.id})
		)

		self.assertRedirects(response, reverse('patient_detail', kwargs={'patient_id': self.patient.id}))
		self.assertFalse(Vitals.objects.filter(id=vitals.id).exists())

	def test_empty_vitals_submission_is_not_saved(self):
		user = User.objects.create_user(
			username='doc3@example.com',
			email='doc3@example.com',
			password='SecurePass123!'
		)
		DoctorProfile.objects.create(user=user, specialization='General', hospital='UHC')

		self.client.post(reverse('login'), {
			'email': 'doc3@example.com',
			'password': 'SecurePass123!'
		})

		response = self.client.post(
			reverse('add_vitals', kwargs={'patient_id': self.patient.id}),
			{
				'blood_pressure': '',
				'blood_sugar': '',
				'heart_rate': '',
				'temperature': '',
				'spo2': '',
				'weight': ''
			},
			follow=True
		)

		self.assertContains(response, 'All vitals fields are required.')
		self.assertEqual(Vitals.objects.filter(patient=self.patient).count(), 0)
