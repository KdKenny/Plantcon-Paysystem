from django.urls import path
from . import views

app_name = 'processpay'

urlpatterns = [
    path('pending/', views.pending_payments, name='pending_payments'),
    path('process/<int:payment_id>/', views.process_payment, name='process_payment'),
]