from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from .models import Profile
import os

# ---------- Auth forms ----------

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean_username(self):
        email = self.data.get('username', '')
        return email.strip().lower()


# Allowed extensions for uploads
ALLOWED_DOC_EXTS = {'.pdf', '.jpg', '.jpeg', '.png'}

def _validate_upload(f, label="file", max_mb=8):
    if not f:
        return f
    name = (f.name or '').lower()
    ext = os.path.splitext(name)[1]
    if ext not in ALLOWED_DOC_EXTS:
        raise forms.ValidationError(f"Unsupported {label} type. Allowed: PDF, JPG, JPEG, PNG.")
    if f.size > max_mb * 1024 * 1024:
        raise forms.ValidationError(f"{label.capitalize()} too large (max {max_mb} MB).")
    return f


class RegisterForm(forms.ModelForm):
    # Profile + User fields gathered in one page
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Minimum 8 characters.'
    )
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    # NEW: actual upload field for Drug Selling Licence
    drug_license_file = forms.FileField(
        required=True,
        label="Drug Selling Licence",
        widget=forms.ClearableFileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png'})
    )

    class Meta:
        model = User
        # Keep username so the ModelForm is tied to User, but we'll make it NOT required.
        fields = ['username']
        widgets = {'username': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Not required in browser; we'll set username=email in clean()
        self.fields['username'].required = False

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Email already registered.')
        return email

    def clean_password(self):
        pw = self.cleaned_data.get('password') or ''
        if len(pw) < 8:
            raise forms.ValidationError('Password must be at least 8 characters.')
        return pw

    def clean_drug_license_file(self):
        return _validate_upload(self.cleaned_data.get('drug_license_file'), label="document", max_mb=8)

    def clean(self):
        """
        Inject username=email *during validation* so the required check doesn't fire.
        """
        cleaned = super().clean()
        email = (cleaned.get('email') or '').strip().lower()
        cleaned['username'] = email
        return cleaned

    def save(self, commit=True):
        """
        Create the User, then create-or-update the Profile in an idempotent way.
        Avoids UNIQUE(user_id) collisions if a Profile is auto-created elsewhere.
        """
        email = self.cleaned_data['email']  # normalized
        password = self.cleaned_data['password']
        full_name = self.cleaned_data['full_name']
        phone = self.cleaned_data['phone']
        address = self.cleaned_data['address']
        drug_file = self.cleaned_data.get('drug_license_file')

        with transaction.atomic():
            # Create the user first
            user = User(username=email, email=email)
            user.set_password(password)
            if commit:
                user.save()

            # Create or update the single Profile for this user (idempotent)
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": full_name,
                    "phone": phone,
                    "address": address,
                    # legacy text kept blank; we now store the file
                    "medical_license": "",
                    "drug_license_file": drug_file,
                },
            )
        return user


# ---------- Profile edit form ----------

class ProfileForm(forms.ModelForm):
    # Expose the dedicated Drug Selling Licence file on profile edit too
    drug_license_file = forms.FileField(
        required=False,
        label="Drug Selling Licence",
        widget=forms.ClearableFileInput(attrs={'accept': '.pdf,.jpg,.jpeg,.png'})
    )

    class Meta:
        model = Profile
        fields = [
            'full_name',
            'phone',
            'address',
            'gov_id_type',
            'gov_id_file',
            'drug_license_file',   # added here
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'gov_id_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Aadhaar, PAN'}),
            # gov_id_file & drug_license_file use ClearableFileInput by default
        }

    def clean_gov_id_file(self):
        return _validate_upload(self.cleaned_data.get('gov_id_file'), label="gov ID", max_mb=8)

    def clean_drug_license_file(self):
        # Optional on edit; validate only if provided
        f = self.cleaned_data.get('drug_license_file')
        if not f:
            return f
        return _validate_upload(f, label="Drug Selling Licence", max_mb=8)
