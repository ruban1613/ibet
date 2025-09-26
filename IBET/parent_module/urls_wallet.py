"""
URL configuration for Parent Module wallet functionality.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet import (
    ParentWalletViewSet, GenerateParentWalletOTPView, VerifyParentWalletOTPView, StudentWalletApprovalView
)

app_name = 'parent_wallet'

router = DefaultRouter()
router.register(r'', ParentWalletViewSet, basename='parent-wallet')

urlpatterns = [
    path('', include(router.urls)),
    path('generate-otp/', GenerateParentWalletOTPView.as_view(), name='generate-parent-wallet-otp'),
    path('verify-otp/', VerifyParentWalletOTPView.as_view(), name='verify-parent-wallet-otp'),
    path('approve-student/', StudentWalletApprovalView.as_view(), name='approve-student-wallet'),
    path('linked-students-wallets/', ParentWalletViewSet.as_view({'get': 'linked_students_wallets'}), name='linked-students-wallets'),
]
