from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_patient, name='search_patient'),

    # ── APIs for mobile app ──
    path('api/register/', views.patient_register, name='patient_register'),
    path('api/pin-login/', views.patient_pin_login, name='patient_pin_login'),
    path('api/<str:nfc_uid>/', views.patient_api, name='patient_api'),

    # ── existing URLs unchanged ──
    path('<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('<int:patient_id>/add/vitals/', views.add_vitals, name='add_vitals'),
    path('<int:patient_id>/delete/vitals/<int:vitals_id>/', views.delete_vitals, name='delete_vitals'),
    path('<int:patient_id>/add/lab/', views.add_lab, name='add_lab'),
    path('<int:patient_id>/delete/lab/<int:lab_id>/', views.delete_lab, name='delete_lab'),
    path('<int:patient_id>/add/imaging/', views.add_imaging, name='add_imaging'),
    path('<int:patient_id>/delete/imaging/<int:imaging_id>/', views.delete_imaging, name='delete_imaging'),
    path('<int:patient_id>/add/prescription/', views.add_prescription, name='add_prescription'),
    path('<int:patient_id>/delete/prescription/<int:prescription_id>/', views.delete_prescription, name='delete_prescription'),
    path('<int:patient_id>/add/surgery/', views.add_surgery, name='add_surgery'),
    path('<int:patient_id>/delete/surgery/<int:surgery_id>/', views.delete_surgery, name='delete_surgery'),
    path('<int:patient_id>/add/diagnosis/', views.add_diagnosis, name='add_diagnosis'),
    path('<int:patient_id>/delete/diagnosis/<int:diagnosis_id>/', views.delete_diagnosis, name='delete_diagnosis'),
]
