from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q, Count, Sum
from django.utils import timezone
from .models import (
    Company, User, DataSource, RawRecord, NormalizedEmissionRecord,
    AuditLog, Notification
)
from .serializers import (
    CompanySerializer, UserSerializer, UserRegistrationSerializer,
    DataSourceSerializer, RawRecordSerializer, NormalizedEmissionRecordSerializer,
    NormalizedEmissionRecordUpdateSerializer, AuditLogSerializer, NotificationSerializer
)
from .processors.sap_processor import process_sap_data
from .processors.utility_processor import process_utility_data
from .processors.travel_processor import process_travel_data
import threading


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    user = authenticate(username=username, password=password)
    
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(company=self.request.user.company)


class DataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return DataSource.objects.all()
        return DataSource.objects.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        data_source = serializer.save(
            uploaded_by=self.request.user,
            company=self.request.user.company
        )
        
        if data_source.file_path:
            thread = threading.Thread(
                target=self.process_file_async,
                args=(data_source,)
            )
            thread.start()
    
    def process_file_async(self, data_source):
        try:
            data_source.processing_status = 'processing'
            data_source.save()
            
            file_path = data_source.file_path.path
            
            if data_source.source_type == 'sap':
                processed, failed = process_sap_data(data_source, file_path)
            elif data_source.source_type == 'utility':
                processed, failed = process_utility_data(data_source, file_path)
            elif data_source.source_type == 'travel':
                processed, failed = process_travel_data(data_source, file_path)
            else:
                raise ValueError(f"Unknown source type: {data_source.source_type}")
            
            Notification.objects.create(
                user=data_source.uploaded_by,
                notification_type='upload',
                message=f"Processing complete: {processed} records processed, {failed} failed"
            )
            
        except Exception as e:
            data_source.processing_status = 'failed'
            data_source.error_message = str(e)
            data_source.save()
            
            Notification.objects.create(
                user=data_source.uploaded_by,
                notification_type='error',
                message=f"Processing failed: {str(e)}"
            )


class RawRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RawRecord.objects.all()
    serializer_class = RawRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = RawRecord.objects.all()
        
        if self.request.user.role != 'admin':
            queryset = queryset.filter(source__company=self.request.user.company)
        
        source_id = self.request.query_params.get('source_id')
        if source_id:
            queryset = queryset.filter(source_id=source_id)
        
        return queryset


class NormalizedEmissionRecordViewSet(viewsets.ModelViewSet):
    queryset = NormalizedEmissionRecord.objects.all()
    serializer_class = NormalizedEmissionRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['category', 'activity_type', 'location', 'facility']
    ordering_fields = ['activity_date', 'created_at', 'emission_value']
    
    def get_queryset(self):
        queryset = NormalizedEmissionRecord.objects.select_related(
            'company', 'source', 'approved_by'
        )
        
        if self.request.user.role != 'admin':
            queryset = queryset.filter(company=self.request.user.company)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        scope_filter = self.request.query_params.get('scope')
        if scope_filter:
            queryset = queryset.filter(scope=scope_filter)
        
        suspicious = self.request.query_params.get('suspicious')
        if suspicious == 'true':
            queryset = queryset.filter(suspicious_flag=True)
        
        source_id = self.request.query_params.get('source_id')
        if source_id:
            queryset = queryset.filter(source_id=source_id)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return NormalizedEmissionRecordUpdateSerializer
        return NormalizedEmissionRecordSerializer
    
    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_data = NormalizedEmissionRecordSerializer(old_instance).data
        
        instance = serializer.save()
        new_data = NormalizedEmissionRecordSerializer(instance).data
        
        AuditLog.objects.create(
            record=instance,
            action='update',
            changed_by=self.request.user,
            old_value=old_data,
            new_value=new_data
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        record = self.get_object()
        
        if record.locked_for_audit:
            return Response(
                {'error': 'Record is locked for audit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.user.role not in ['admin', 'analyst']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        old_status = record.status
        record.status = 'approved'
        record.approved_by = request.user
        record.approved_at = timezone.now()
        record.save()
        
        AuditLog.objects.create(
            record=record,
            action='approve',
            changed_by=request.user,
            old_value={'status': old_status},
            new_value={'status': 'approved'}
        )
        
        return Response(NormalizedEmissionRecordSerializer(record).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        record = self.get_object()
        
        if record.locked_for_audit:
            return Response(
                {'error': 'Record is locked for audit'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.user.role not in ['admin', 'analyst']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        old_status = record.status
        record.status = 'rejected'
        record.notes = request.data.get('notes', record.notes)
        record.save()
        
        AuditLog.objects.create(
            record=record,
            action='reject',
            changed_by=request.user,
            old_value={'status': old_status},
            new_value={'status': 'rejected'},
            notes=request.data.get('notes', '')
        )
        
        return Response(NormalizedEmissionRecordSerializer(record).data)
    
    @action(detail=True, methods=['post'])
    def lock(self, request, pk=None):
        record = self.get_object()
        
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can lock records'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if record.status != 'approved':
            return Response(
                {'error': 'Only approved records can be locked'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        record.locked_for_audit = True
        record.save()
        
        AuditLog.objects.create(
            record=record,
            action='lock',
            changed_by=request.user
        )
        
        return Response(NormalizedEmissionRecordSerializer(record).data)
    
    @action(detail=False, methods=['post'])
    def bulk_approve(self, request):
        record_ids = request.data.get('record_ids', [])
        
        if request.user.role not in ['admin', 'analyst']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        records = NormalizedEmissionRecord.objects.filter(
            id__in=record_ids,
            locked_for_audit=False
        )
        
        if request.user.role != 'admin':
            records = records.filter(company=request.user.company)
        
        count = 0
        for record in records:
            record.status = 'approved'
            record.approved_by = request.user
            record.approved_at = timezone.now()
            record.save()
            
            AuditLog.objects.create(
                record=record,
                action='approve',
                changed_by=request.user
            )
            count += 1
        
        return Response({'approved_count': count})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = AuditLog.objects.select_related('record', 'changed_by')
        
        if self.request.user.role != 'admin':
            queryset = queryset.filter(record__company=self.request.user.company)
        
        record_id = self.request.query_params.get('record_id')
        if record_id:
            queryset = queryset.filter(record_id=record_id)
        
        return queryset


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response(NotificationSerializer(notification).data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'status': 'success'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    
    if user.role == 'admin':
        records = NormalizedEmissionRecord.objects.all()
        sources = DataSource.objects.all()
    else:
        records = NormalizedEmissionRecord.objects.filter(company=user.company)
        sources = DataSource.objects.filter(company=user.company)
    
    total_records = records.count()
    pending_records = records.filter(status='pending').count()
    approved_records = records.filter(status='approved').count()
    flagged_records = records.filter(suspicious_flag=True).count()
    
    total_emissions = records.filter(
        emission_value__isnull=False
    ).aggregate(total=Sum('emission_value'))['total'] or 0
    
    scope_breakdown = {
        'scope_1': records.filter(scope='scope_1').aggregate(total=Sum('emission_value'))['total'] or 0,
        'scope_2': records.filter(scope='scope_2').aggregate(total=Sum('emission_value'))['total'] or 0,
        'scope_3': records.filter(scope='scope_3').aggregate(total=Sum('emission_value'))['total'] or 0,
    }
    
    source_stats = sources.values('source_type').annotate(
        count=Count('id'),
        total_rows=Sum('total_rows'),
        processed_rows=Sum('processed_rows')
    )
    
    recent_uploads = DataSourceSerializer(
        sources.order_by('-uploaded_at')[:5],
        many=True
    ).data
    
    return Response({
        'total_records': total_records,
        'pending_records': pending_records,
        'approved_records': approved_records,
        'flagged_records': flagged_records,
        'total_emissions': float(total_emissions),
        'scope_breakdown': {k: float(v) for k, v in scope_breakdown.items()},
        'source_stats': list(source_stats),
        'recent_uploads': recent_uploads,
    })
