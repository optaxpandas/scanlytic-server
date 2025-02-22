import uuid
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractBaseUser

class User(AbstractBaseUser):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_name = models.CharField(max_length=255, unique=False, blank=True, null=True)  # Make user_name optional
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    last_login = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.user_name} ({self.email})"

    class Meta:
        db_table = 'users'  # Specify custom table name

class UserAuth(models.Model):
    auth_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='auth')
    access_token = models.TextField()  # Increase max length
    refresh_token = models.TextField()  # Increase max length
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Auth for {self.user.user_name}"

    class Meta:
        db_table = 'user_auth'  # Specify custom table name

class Table(models.Model):
    FILE_TYPES = [
        ('csv', 'CSV'),
        ('xlsx', 'XLSX'),
        ('copy', 'Copy'),
    ]

    table_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tables')
    image = models.ImageField(upload_to='table_images/', blank=True, null=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Table {self.table_id} by {self.user.user_name}"

    class Meta:
        db_table = 'tables'  # Specify custom table name

class QR(models.Model):
    qr_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qrs')
    image = models.ImageField(upload_to='qr_images/', blank=False, null=False)
    extracted_data = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QR Code {self.qr_id} for {self.user.user_name}"

    class Meta:
        db_table = 'qr'  # Specify custom table name

class QRReport(models.Model):
    qr_report_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qr = models.ForeignKey(QR, on_delete=models.CASCADE, related_name='reports')
    report_date = models.DateTimeField(auto_now_add=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for QR {self.qr.qr_id}"

    class Meta:
        db_table = 'qr_report'  # Specify custom table name

@receiver(pre_save, sender=User)
def update_related_user(sender, instance, **kwargs):
    if instance.pk:
        UserAuth.objects.filter(user=instance).update(user=instance)
        Table.objects.filter(user=instance).update(user=instance)
        QR.objects.filter(user=instance).update(user=instance)
