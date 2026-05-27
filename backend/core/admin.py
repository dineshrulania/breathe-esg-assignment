from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Company, User, DataSource, RawRecord, NormalizedEmissionRecord,
    AuditLog, Notification, UnitConversion, EmissionFactor
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'is_active']
    search_fields = ['name']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'company', 'role', 'is_active']
    list_filter = ['role', 'company', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('company', 'role')}),
    )


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['source_type', 'file_name', 'company', 'uploaded_by', 'uploaded_at', 'processing_status']
    list_filter = ['source_type', 'processing_status', 'company']
    search_fields = ['file_name']


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'source', 'validation_status', 'created_at']
    list_filter = ['validation_status', 'source__source_type']


@admin.register(NormalizedEmissionRecord)
class NormalizedEmissionRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'company', 'scope', 'category', 'activity_type', 'quantity', 'status', 'suspicious_flag']
    list_filter = ['scope', 'status', 'suspicious_flag', 'company']
    search_fields = ['category', 'activity_type', 'location']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['record', 'action', 'changed_by', 'changed_at']
    list_filter = ['action', 'changed_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'message', 'read', 'created_at']
    list_filter = ['notification_type', 'read']


@admin.register(UnitConversion)
class UnitConversionAdmin(admin.ModelAdmin):
    list_display = ['from_unit', 'to_unit', 'conversion_factor', 'category']


@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    list_display = ['activity_type', 'scope', 'factor_value', 'unit', 'year', 'region']
    list_filter = ['scope', 'year', 'region']
