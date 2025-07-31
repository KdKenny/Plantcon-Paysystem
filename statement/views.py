import csv
import io
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from addinvoice.models import Invoice
from processpay.models import Payment
from django.db.models import Sum
from datetime import date

@login_required
def dashboard(request):
    invoices = Invoice.objects.all()
    
    # Calculate dashboard metrics
    pending_payments_count = Payment.objects.filter(processed=False).count()
    total_paid = Payment.objects.filter(processed=True, is_deducted=False).aggregate(Sum('amount_received'))['amount_received__sum'] or 0
    
    today = date.today()
    pending_this_month_amount = Payment.objects.filter(
        processed=False,
        due_date__year=today.year,
        due_date__month=today.month
    ).aggregate(Sum('invoice__monthly_amount'))['invoice__monthly_amount__sum'] or 0

    total_deducted = Payment.objects.filter(is_deducted=True).aggregate(Sum('amount_received'))['amount_received__sum'] or 0

    # Annotate invoices with total received amount
    for invoice in invoices:
        invoice.total_received_amount = invoice.payments.filter(processed=True, is_deducted=False).aggregate(Sum('amount_received'))['amount_received__sum'] or 0

    context = {
        'invoices': invoices,
        'pending_payments_count': pending_payments_count,
        'total_paid': total_paid,
        'pending_this_month_amount': pending_this_month_amount,
        'total_deducted': total_deducted,
    }
    return render(request, 'statement/dashboard.html', context)

@login_required
def export_payments_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments.csv"'

    writer = csv.writer(response)
    writer.writerow(['Payment ID', 'Invoice Name', 'Due Date', 'Processed Date', 'Amount Received', 'Is Deducted', 'Processed'])

    payments = Payment.objects.all().select_related('invoice')
    for payment in payments:
        writer.writerow([
            payment.id,
            payment.invoice.name,
            payment.due_date,
            payment.processed_date,
            payment.amount_received,
            payment.is_deducted,
            payment.processed,
        ])

    return response

@login_required
def import_payments_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, 'No file uploaded.')
            return redirect('statement:dashboard')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'This is not a CSV file.')
            return redirect('statement:dashboard')

        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            next(reader)  # Skip header row

            for row in reader:
                payment_id = row[0]
                invoice_name = row[1]
                due_date = row[2] if row[2] else None
                processed_date = row[3] if row[3] else None
                amount_received = row[4]
                is_deducted = row[5].lower() in ('true', '1', 't')
                processed = row[6].lower() in ('true', '1', 't')

                invoice, _ = Invoice.objects.get_or_create(name=invoice_name)

                Payment.objects.update_or_create(
                    id=payment_id,
                    defaults={
                        'invoice': invoice,
                        'due_date': due_date,
                        'processed_date': processed_date,
                        'amount_received': amount_received,
                        'is_deducted': is_deducted,
                        'processed': processed,
                    }
                )
            messages.success(request, 'CSV file has been imported successfully.')
        except Exception as e:
            messages.error(request, f'Error processing file: {e}')

    return redirect('statement:dashboard')


@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    payments = invoice.payments.all().order_by('due_date')
    context = {
        'invoice': invoice,
        'payments': payments,
    }
    return render(request, 'statement/invoice_detail.html', context)

@login_required
def toggle_deducted(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    payment.is_deducted = not payment.is_deducted
    payment.save()
    return redirect('statement:invoice_detail', invoice_id=payment.invoice.id)
