from django.core.management.base import BaseCommand
from addinvoice.models import Invoice
from processpay.models import Payment
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Generates monthly payments for active invoices, including past due ones.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        invoices = Invoice.objects.filter(start_date__lte=today)

        for invoice in invoices:
            # Determine the date range to check for payments
            start_month = invoice.start_date
            end_month = min(today, invoice.end_date)

            current_month = start_month
            while current_month <= end_month:
                # Check if a payment for this month already exists
                if not Payment.objects.filter(invoice=invoice, due_date__year=current_month.year, due_date__month=current_month.month).exists():
                    due_date = current_month.replace(day=1)
                    Payment.objects.create(
                        invoice=invoice,
                        due_date=due_date,
                        processed=False
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created payment for {invoice.name} for {due_date.strftime("%Y-%m")}'))
                
                # Move to the next month
                # A simple way to advance the month
                if current_month.month == 12:
                    current_month = current_month.replace(year=current_month.year + 1, month=1)
                else:
                    current_month = current_month.replace(month=current_month.month + 1)