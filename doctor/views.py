from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from .models import DoctorProfile


def signup_view(request):
	if request.method == 'POST':
		full_name = request.POST.get('name', '').strip()
		email = request.POST.get('email', '').strip().lower()
		password = request.POST.get('password', '')
		specialization = request.POST.get('specialization', '').strip()
		hospital = request.POST.get('hospital', '').strip()

		if not (full_name and email and password and specialization and hospital):
			return render(request, 'doctor/auth.html', {'error': 'All signup fields are required.', 'auth_mode': 'signup'})

		name = full_name.split(' ', 1)

		try:
			user = User.objects.create_user(
				username=email,
				password=password,
				email=email,
				first_name=name[0],
				last_name=name[1] if len(name) > 1 else ''
			)
		except IntegrityError:
			return render(request, 'doctor/auth.html', {'error': 'A doctor account with this email already exists.', 'auth_mode': 'signup'})

		DoctorProfile.objects.create(
			user=user,
			specialization=specialization,
			hospital=hospital
		)
		login(request, user)
		return redirect('dashboard')
	return render(request, 'doctor/auth.html')


def login_view(request):
	if request.method == 'POST':
		email = request.POST.get('email', '').strip().lower()
		password = request.POST.get('password', '')
		user = authenticate(request, username=email, password=password)
		if user:
			login(request, user)
			return redirect('dashboard')
		return render(request, 'doctor/auth.html', {'error': 'Invalid credentials', 'auth_mode': 'login'})
	return render(request, 'doctor/auth.html')


def logout_view(request):
	logout(request)
	return redirect('login')


@login_required
def dashboard_view(request):
	profile, _ = DoctorProfile.objects.get_or_create(
		user=request.user,
		defaults={'specialization': 'General', 'hospital': 'Not set'}
	)
	return render(request, 'doctor/dashboard.html', {'profile': profile})
