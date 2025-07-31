from django.db import models
from addinvoice.models import Invoice
from django.utils import timezone

class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name="關聯單")
    due_date = models.DateField(verbose_name="應付日期")
    processed_date = models.DateField(null=True, blank=True, verbose_name="實際付款日期")
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="實收金額")
    is_deducted = models.BooleanField(default=False, verbose_name="是否已扣款轉帳")
    processed = models.BooleanField(default=False, verbose_name="已處理")

    def __str__(self):
        return f"{self.invoice.name} - {self.due_date}"
