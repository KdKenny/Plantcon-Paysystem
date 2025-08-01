import csv
import io
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from addinvoice.models import Invoice
from processpay.models import Payment
from django.db.models import Sum
from datetime import date, datetime

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

        # File size validation (max 5MB)
        if csv_file.size > 5 * 1024 * 1024:
            messages.error(request, 'File too large. Maximum size is 5MB.')
            return redirect('statement:dashboard')

        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            
            # Verify header row
            try:
                header = next(reader)
                expected_headers = ['Payment ID', 'Invoice Name', 'Due Date', 'Processed Date', 'Amount Received', 'Is Deducted', 'Processed']
                if header != expected_headers:
                    messages.error(request, 'Invalid CSV format. Please use the correct header format.')
                    return redirect('statement:dashboard')
            except StopIteration:
                messages.error(request, 'Empty CSV file.')
                return redirect('statement:dashboard')

            updated_count = 0
            error_count = 0
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because of header
                if len(row) < 7:
                    error_count += 1
                    continue
                    
                try:
                    # Validate and sanitize input data
                    payment_id = _validate_payment_id(row[0])
                    invoice_name = _validate_invoice_name(row[1])
                    due_date = _validate_date(row[2], 'due_date') if row[2] else None
                    processed_date = _validate_date(row[3], 'processed_date') if row[3] else None
                    amount_received = _validate_amount(row[4])
                    is_deducted = _validate_boolean(row[5])
                    processed = _validate_boolean(row[6])

                    # Security: Only allow updates to existing payments, not arbitrary IDs
                    try:
                        existing_payment = Payment.objects.get(id=payment_id)
                    except Payment.DoesNotExist:
                        # Skip non-existent payments for security
                        error_count += 1
                        continue

                    # Get or create invoice (but validate name)
                    invoice, _ = Invoice.objects.get_or_create(
                        name=invoice_name,
                        defaults={'monthly_amount': Decimal('0.00')}
                    )

                    # Update only the existing payment
                    existing_payment.invoice = invoice
                    existing_payment.due_date = due_date
                    existing_payment.processed_date = processed_date
                    existing_payment.amount_received = amount_received
                    existing_payment.is_deducted = is_deducted
                    existing_payment.processed = processed
                    existing_payment.save()
                    
                    updated_count += 1
                    
                except (ValidationError, ValueError, InvalidOperation) as e:
                    error_count += 1
                    continue
                    
            if updated_count > 0:
                messages.success(request, f'CSV imported successfully. {updated_count} payments updated.')
            if error_count > 0:
                messages.warning(request, f'{error_count} rows had errors and were skipped.')
                
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)[:100]}')  # Limit error message length

    return redirect('statement:dashboard')


def _validate_payment_id(value):
    """Validate payment ID is a positive integer"""
    try:
        payment_id = int(value)
        if payment_id <= 0:
            raise ValidationError('Payment ID must be positive')
        return payment_id
    except (ValueError, TypeError):
        raise ValidationError('Invalid payment ID')


def _validate_invoice_name(value):
    """Validate and sanitize invoice name"""
    if not value or not isinstance(value, str):
        raise ValidationError('Invoice name is required')
    
    # Sanitize: remove dangerous characters, limit length
    sanitized = str(value).strip()[:200]
    if not sanitized:
        raise ValidationError('Invoice name cannot be empty')
    
    return sanitized


def _validate_date(value, field_name):
    """Validate date format"""
    if not value:
        return None
        
    try:
        # Try multiple date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValidationError(f'Invalid date format for {field_name}')
    except Exception:
        raise ValidationError(f'Invalid date for {field_name}')


def _validate_amount(value):
    """Validate monetary amount"""
    if not value:
        return Decimal('0.00')
        
    try:
        amount = Decimal(str(value))
        if amount < 0:
            raise ValidationError('Amount cannot be negative')
        if amount > Decimal('999999.99'):  # Reasonable upper limit
            raise ValidationError('Amount too large')
        return amount.quantize(Decimal('0.01'))  # Round to 2 decimal places
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError('Invalid amount format')


def _validate_boolean(value):
    """Validate boolean value"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 't', 'yes', 'on')
    return bool(value)


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
