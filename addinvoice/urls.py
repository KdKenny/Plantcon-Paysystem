from django.urls import path
from . import views

app_name = 'addinvoice'

urlpatterns = [
    path('create/', views.create_invoice, name='create_invoice'),
    path('edit/<int:invoice_id>/', views.edit_invoice, name='edit_invoice'),
]