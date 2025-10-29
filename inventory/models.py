from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Manufacturer(models.Model):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Medicine(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    medicine_id = models.CharField(max_length=100, unique=True)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.SET_NULL, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    mfg_date = models.DateField()
    exp_date = models.DateField()
    quantity_on_hand = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.medicine_id})"

    @property
    def expiry_status(self):
        today = timezone.localdate()
        if self.exp_date < today:
            return 'expired'
        if self.exp_date <= today + timedelta(days=30):
            return 'expiring'
        return 'ok'

TRANSACTION_TYPES = (
    ('IMPORT', 'Import'),
    ('EXPORT', 'Export'),
)

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('BOUGHT', 'Bought'),
        ('SOLD', 'Sold'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    ttype = models.CharField(max_length=10, choices=TYPE_CHOICES)
    partner_name = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_amount(self):
        return self.unit_price * self.quantity
