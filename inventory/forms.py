from django import forms
from .models import Medicine, Transaction, Manufacturer


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'medicine_id', 'manufacturer', 'cost_price', 'mrp', 'mfg_date', 'exp_date']  # quantity_on_hand stays managed by logic
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'medicine_id': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer': forms.Select(attrs={'class': 'form-select'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'mrp': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'mfg_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'exp_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean(self):
        data = super().clean()
        cost = data.get('cost_price') or 0
        mrp = data.get('mrp') or 0
        if cost < 0 or mrp < 0:
            raise forms.ValidationError("Prices cannot be negative.")
        return data


class TransactionForm(forms.ModelForm):
    TTYPE_CHOICES = (
        ('', '— Select Type —'),   # default blank; user must choose
        ('BOUGHT', 'Bought'),
        ('SOLD', 'Sold'),
    )

    ttype = forms.ChoiceField(
        choices=TTYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        """Scope medicine choices to the current user automatically."""
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['medicine'].queryset = Medicine.objects.filter(owner=user)

    class Meta:
        model = Transaction
        fields = ['medicine', 'ttype', 'partner_name', 'unit_price', 'quantity']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-select'}),
            'partner_name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

    def clean_ttype(self):
        val = (self.cleaned_data.get('ttype') or '').strip()
        if not val:
            raise forms.ValidationError('Please choose Bought or Sold.')
        return val

    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price is None or price < 0:
            raise forms.ValidationError('Unit price must be zero or positive.')
        return price

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is None or qty <= 0:
            raise forms.ValidationError('Quantity must be a positive number.')
        return qty


class ManufacturerForm(forms.ModelForm):
    class Meta:
        model = Manufacturer
        fields = ['name', 'contact_person', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError("Name is required.")
        qs = Manufacturer.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Manufacturer already exists.")
        return name

