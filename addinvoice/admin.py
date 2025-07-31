from django.contrib import admin
from .models import Invoice

class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'monthly_amount', 'created_at')
    list_filter = ('start_date', 'end_date')
    search_fields = ('name',)

admin.site.register(Invoice, InvoiceAdmin)
