from django.db import models
from django.contrib.auth.models import User

def drug_license_upload_path(instance, filename):
    return f"drug_licenses/user_{instance.user_id}/{filename}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # legacy text (optional)
    medical_license = models.CharField(max_length=100, blank=True)

    # generic gov id (optional)
    gov_id_type = models.CharField(max_length=100, blank=True)
    gov_id_file = models.FileField(upload_to='gov_docs/', blank=True, null=True)

    # NEW: file upload
    drug_license_file = models.FileField(
        upload_to=drug_license_upload_path,
        blank=True, null=True,
        verbose_name="Drug Selling Licence"
    )

    def __str__(self):
        return self.full_name or self.user.username
