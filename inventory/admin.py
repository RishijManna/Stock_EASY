from django.contrib import admin
from .models import Medicine, Manufacturer, Transaction

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone')

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name','medicine_id','manufacturer','mrp','exp_date','quantity_on_hand','owner')
    search_fields = ('name','medicine_id')
    list_filter = ('manufacturer','exp_date')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('ttype','medicine','quantity','unit_price','partner_name','owner','created_at')
    list_filter = ('ttype','created_at')
