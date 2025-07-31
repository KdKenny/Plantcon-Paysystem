from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Invoice
from .forms import InvoiceForm
from django.contrib import messages

@login_required
def create_invoice(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice created successfully.')
            return redirect('statement:dashboard')
    else:
        form = InvoiceForm()
    return render(request, 'addinvoice/create_invoice.html', {'form': form})

@login_required
def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice updated successfully.')
            return redirect('statement:dashboard')
    else:
        form = InvoiceForm(instance=invoice)
    return render(request, 'addinvoice/edit_invoice.html', {'form': form})
