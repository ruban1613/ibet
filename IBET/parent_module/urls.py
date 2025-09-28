from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ParentDashboardViewSet, AlertSettingsViewSet, StudentMonitoringViewSet,
    ParentAlertViewSet, StudentWalletAccessView, StudentOverviewView, LinkedStudentsView,
    ParentOTPRequestViewSet, GenerateOTPView
)

router = DefaultRouter()
router.register(r'dashboard', ParentDashboardViewSet, basename='parent-dashboard')
router.register(r'alert-settings', AlertSettingsViewSet, basename='alert-settings')
router.register(r'monitoring', StudentMonitoringViewSet, basename='student-monitoring')
router.register(r'alerts', ParentAlertViewSet, basename='parent-alerts')
router.register(r'otp-requests', ParentOTPRequestViewSet, basename='otp-requests')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('wallet-access/', StudentWalletAccessView.as_view(), name='student-wallet-access'),
    path('students/', LinkedStudentsView.as_view(), name='linked-students'),
    path('students/<int:student_id>/overview/', StudentOverviewView.as_view(), name='student-overview'),
    path('generate-otp/', GenerateOTPView.as_view(), name='generate-otp'),
    # Include wallet URLs
    path('wallet/', include('parent_module.urls_wallet')),
]
