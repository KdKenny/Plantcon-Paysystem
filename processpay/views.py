from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Payment
from addinvoice.models import Invoice
from django.utils import timezone
from django.contrib import messages

def _generate_pending_payments():
    """
    Generates monthly payments for active invoices, including past due ones.
    This is the core logic from the management command.
    """
    today = timezone.now().date()
    invoices = Invoice.objects.filter(start_date__lte=today)

    for invoice in invoices:
        start_month = invoice.start_date
        end_month = min(today, invoice.end_date) if invoice.end_date else today

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
            
            # Move to the next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)

@login_required
def pending_payments(request):
    # 1. Generate any missing payment records
    _generate_pending_payments()
    
    # 2. Fetch pending payments that are due
    today = timezone.now().date()
    pending_payments_list = Payment.objects.filter(processed=False, due_date__lte=today).order_by('due_date')

    # 3. Add logic to determine if 'is_deducted' should be pre-checked
    for payment in pending_payments_list:
        processed_count = Payment.objects.filter(invoice=payment.invoice, processed=True).count()
        if payment.invoice.deduction_periods and processed_count < payment.invoice.deduction_periods:
            payment.should_be_deducted = True
        else:
            payment.should_be_deducted = False

    return render(request, 'processpay/pending_payments.html', {'payments': pending_payments_list})

@login_required
def process_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        amount_received = request.POST.get('amount_received')
        is_deducted = request.POST.get('is_deducted') == 'on'
        
        payment.amount_received = amount_received
        payment.is_deducted = is_deducted
        payment.processed = True
        payment.processed_date = timezone.now().date()
        payment.save()
        
        messages.success(request, 'Payment processed successfully.')
        return redirect('processpay:pending_payments')
        
    return redirect('processpay:pending_payments')
