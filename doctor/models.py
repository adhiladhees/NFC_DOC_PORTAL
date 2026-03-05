from django.db import models
from django.contrib.auth.models import User


class DoctorProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	specialization = models.CharField(max_length=100)
	hospital = models.CharField(max_length=200)
	phone = models.CharField(max_length=15, blank=True)

	def __str__(self):
		return f"Dr. {self.user.get_full_name()}"
