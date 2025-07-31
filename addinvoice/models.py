from django.db import models
from django.utils import timezone

class Invoice(models.Model):
    name = models.CharField(max_length=200, verbose_name="單名稱")
    start_date = models.DateField(verbose_name="開始日期")
    end_date = models.DateField(verbose_name="結束日期")
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="每月應收金額")
    deduction_recipient = models.CharField(max_length=100, blank=True, null=True, verbose_name="轉帳對象")
    deduction_periods = models.IntegerField(default=0, verbose_name="扣款期數")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="創建時間")

    def __str__(self):
        return self.name
