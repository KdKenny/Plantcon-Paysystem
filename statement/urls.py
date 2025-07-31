from django.urls import path
from . import views

app_name = 'statement'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('payment/toggle_deducted/<int:payment_id>/', views.toggle_deducted, name='toggle_deducted'),
    path('export/csv/', views.export_payments_csv, name='export_payments_csv'),
    path('import/csv/', views.import_payments_csv, name='import_payments_csv'),
]