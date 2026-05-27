from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
import json


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('analyst', 'Analyst'),
        ('viewer', 'Viewer'),
    ]
    
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='users',
        null=True,
        blank=True
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    
    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.role})"


class DataSource(models.Model):
    SOURCE_TYPE_CHOICES = [
        ('sap', 'SAP Export'),
        ('utility', 'Utility Data'),
        ('travel', 'Corporate Travel'),
    ]
    
    UPLOAD_METHOD_CHOICES = [
        ('csv', 'CSV Upload'),
        ('api', 'API Integration'),
        ('manual', 'Manual Entry'),
    ]
    
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='data_sources')
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    upload_method = models.CharField(max_length=20, choices=UPLOAD_METHOD_CHOICES)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_path = models.FileField(upload_to='uploads/', null=True, blank=True)
    processing_status = models.CharField(
        max_length=20, 
        choices=PROCESSING_STATUS_CHOICES, 
        default='pending'
    )
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.source_type} - {self.file_name} ({self.uploaded_at.strftime('%Y-%m-%d')})"


class RawRecord(models.Model):
    VALIDATION_STATUS_CHOICES = [
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ('warning', 'Warning'),
    ]
    
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='raw_records')
    raw_payload = models.JSONField()
    validation_status = models.CharField(
        max_length=20, 
        choices=VALIDATION_STATUS_CHOICES, 
        default='valid'
    )
    validation_errors = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Raw Record {self.id} - {self.source.source_type}"


class NormalizedEmissionRecord(models.Model):
    SCOPE_CHOICES = [
        ('scope_1', 'Scope 1 - Direct Emissions'),
        ('scope_2', 'Scope 2 - Purchased Electricity'),
        ('scope_3', 'Scope 3 - Indirect Emissions'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged for Review'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='emission_records')
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='normalized_records')
    raw_record = models.OneToOneField(
        RawRecord, 
        on_delete=models.CASCADE, 
        related_name='normalized_record',
        null=True,
        blank=True
    )
    
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    category = models.CharField(max_length=100)
    activity_type = models.CharField(max_length=100)
    activity_date = models.DateField()
    
    quantity = models.DecimalField(max_digits=15, decimal_places=4, validators=[MinValueValidator(0)])
    normalized_unit = models.CharField(max_length=50)
    original_unit = models.CharField(max_length=50, blank=True)
    
    emission_factor = models.DecimalField(
        max_digits=10, 
        decimal_places=6, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    emission_value = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    emission_unit = models.CharField(max_length=50, default='kg CO2e')
    
    location = models.CharField(max_length=255, blank=True)
    facility = models.CharField(max_length=255, blank=True)
    vendor = models.CharField(max_length=255, blank=True)
    
    suspicious_flag = models.BooleanField(default=False)
    suspicious_reason = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_records'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    locked_for_audit = models.BooleanField(default=False)
    
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['scope', 'activity_date']),
            models.Index(fields=['suspicious_flag']),
        ]
    
    def __str__(self):
        return f"{self.scope} - {self.activity_type} ({self.quantity} {self.normalized_unit})"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('flag', 'Flagged'),
        ('lock', 'Locked'),
        ('unlock', 'Unlocked'),
    ]
    
    record = models.ForeignKey(
        NormalizedEmissionRecord, 
        on_delete=models.CASCADE, 
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.action} by {self.changed_by} at {self.changed_at}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('upload', 'Upload Complete'),
        ('approval', 'Approval Required'),
        ('flagged', 'Record Flagged'),
        ('error', 'Processing Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.user.username}"


class UnitConversion(models.Model):
    from_unit = models.CharField(max_length=50)
    to_unit = models.CharField(max_length=50)
    conversion_factor = models.DecimalField(max_digits=15, decimal_places=10)
    category = models.CharField(max_length=50)
    
    class Meta:
        unique_together = ['from_unit', 'to_unit', 'category']
    
    def __str__(self):
        return f"{self.from_unit} -> {self.to_unit} ({self.conversion_factor})"


class EmissionFactor(models.Model):
    activity_type = models.CharField(max_length=100)
    scope = models.CharField(max_length=20)
    factor_value = models.DecimalField(max_digits=10, decimal_places=6)
    unit = models.CharField(max_length=50)
    source = models.CharField(max_length=255)
    year = models.IntegerField()
    region = models.CharField(max_length=100, default='Global')
    
    class Meta:
        ordering = ['-year']
    
    def __str__(self):
        return f"{self.activity_type} - {self.factor_value} {self.unit}"
