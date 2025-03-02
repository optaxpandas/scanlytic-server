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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auths')
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
    image = models.CharField(max_length=255, blank=False, null=False)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    content = models.CharField(max_length=255, null=False, blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Table {self.table_id} by {self.user.user_name}"

    class Meta:
        db_table = 'tables'  # Specify custom table name

class QR(models.Model):
    RISK_LEVEL = [
        ('safe', 'Safe'),
        ('critical', 'Critical'),
        ('risky', 'Risky')
    ]
    qr_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qrs')
    image = models.CharField(max_length=255, blank=False, null=False)
    url = models.CharField(max_length=255, blank=False, null=False, default='')
    first_submission_date = models.DateTimeField(null=True, blank=True)
    last_analysis_date = models.DateTimeField(null=True, blank=True)
    reputation = models.IntegerField(default=0, blank=False, null=False)
    total_malicious_votes = models.IntegerField(default=0, blank=False, null=False)
    total_harmless_votes = models.IntegerField(default=0, blank=False, null=False)
    malicious = models.IntegerField(default=0, blank=False, null=False)
    suspicious = models.IntegerField(default=0, blank=False, null=False)
    harmless = models.IntegerField(default=0, blank=False, null=False)
    security_score = models.IntegerField(default=0, blank=False, null=False)
    risk_level = models.CharField(default='safe', max_length=10, choices=RISK_LEVEL)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"QR Code {self.qr_id} for {self.user.user_name}"

    class Meta:
        db_table = 'qr'  # Specify custom table name

@receiver(pre_save, sender=User)
def update_related_user(sender, instance, **kwargs):
    if instance.pk:
        UserAuth.objects.filter(user=instance).update(user=instance)
        Table.objects.filter(user=instance).update(user=instance)
        QR.objects.filter(user=instance).update(user=instance)
