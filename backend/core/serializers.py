from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Company, DataSource, RawRecord, NormalizedEmissionRecord,
    AuditLog, Notification, UnitConversion, EmissionFactor
)

User = get_user_model()


class CompanySerializer(serializers.ModelSerializer):
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'created_at', 'updated_at', 'is_active', 'user_count']
    
    def get_user_count(self, obj):
        return obj.users.count()


class UserSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'company', 'company_name', 'date_joined', 'is_active'
        ]
        read_only_fields = ['date_joined']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'company', 'role']
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class DataSourceSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = DataSource
        fields = [
            'id', 'company', 'company_name', 'source_type', 'upload_method',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at', 'file_name',
            'processing_status', 'total_rows', 'processed_rows', 'failed_rows',
            'error_message', 'success_rate'
        ]
        read_only_fields = ['uploaded_at', 'processing_status', 'total_rows', 'processed_rows', 'failed_rows']
    
    def get_success_rate(self, obj):
        if obj.total_rows == 0:
            return 0
        return round((obj.processed_rows / obj.total_rows) * 100, 2)


class RawRecordSerializer(serializers.ModelSerializer):
    source_type = serializers.CharField(source='source.source_type', read_only=True)
    
    class Meta:
        model = RawRecord
        fields = [
            'id', 'source', 'source_type', 'raw_payload', 'validation_status',
            'validation_errors', 'created_at'
        ]


class NormalizedEmissionRecordSerializer(serializers.ModelSerializer):
    source_type = serializers.CharField(source='source.source_type', read_only=True)
    source_file = serializers.CharField(source='source.file_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            'id', 'company', 'company_name', 'source', 'source_type', 'source_file',
            'raw_record', 'scope', 'category', 'activity_type', 'activity_date',
            'quantity', 'normalized_unit', 'original_unit', 'emission_factor',
            'emission_value', 'emission_unit', 'location', 'facility', 'vendor',
            'suspicious_flag', 'suspicious_reason', 'status', 'approved_by',
            'approved_by_name', 'approved_at', 'locked_for_audit', 'notes',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'approved_at']


class NormalizedEmissionRecordUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormalizedEmissionRecord
        fields = [
            'quantity', 'normalized_unit', 'location', 'facility', 'vendor',
            'notes', 'status', 'suspicious_flag', 'suspicious_reason'
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    record_id = serializers.IntegerField(source='record.id', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'record', 'record_id', 'action', 'changed_by', 'changed_by_name',
            'changed_at', 'old_value', 'new_value', 'notes'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'notification_type', 'message', 'read', 'created_at']


class UnitConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitConversion
        fields = ['id', 'from_unit', 'to_unit', 'conversion_factor', 'category']


class EmissionFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmissionFactor
        fields = ['id', 'activity_type', 'scope', 'factor_value', 'unit', 'source', 'year', 'region']
