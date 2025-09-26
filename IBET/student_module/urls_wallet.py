"""
URL configuration for Student Module wallet functionality.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet import (
    StudentWalletViewSet, GenerateStudentWalletOTPView, VerifyStudentWalletOTPView
)

app_name = 'student_wallet'

router = DefaultRouter()
router.register(r'wallet', StudentWalletViewSet, basename='student-wallet')

urlpatterns = [
    path('', include(router.urls)),
    path('generate-otp/', GenerateStudentWalletOTPView.as_view(), name='generate-student-wallet-otp'),
    path('verify-otp/', VerifyStudentWalletOTPView.as_view(), name='verify-student-wallet-otp'),
    path('request-parent-approval/', StudentWalletViewSet.as_view({'post': 'request_parent_approval'}), name='request-parent-approval'),
]
