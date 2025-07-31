from django.contrib import admin
from .models import Payment

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'due_date', 'amount_received', 'processed', 'processed_date', 'is_deducted')
    list_filter = ('processed', 'due_date')
    search_fields = ('invoice__name',)

admin.site.register(Payment, PaymentAdmin)
