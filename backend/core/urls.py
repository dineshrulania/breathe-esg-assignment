from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'data-sources', views.DataSourceViewSet)
router.register(r'raw-records', views.RawRecordViewSet)
router.register(r'emission-records', views.NormalizedEmissionRecordViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)
router.register(r'notifications', views.NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', views.current_user, name='current_user'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
]
