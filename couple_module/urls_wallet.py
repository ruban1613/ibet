"""
Complete URL patterns for Couple Module wallet functionality.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet_final import (
    CoupleWalletViewSet,
    CoupleWalletTransactionViewSet,
    GenerateCoupleWalletOTPView,
    VerifyCoupleWalletOTPView
)

# Create router for couple wallet endpoints
router = DefaultRouter()
router.register(r'', CoupleWalletViewSet, basename='couple-wallet')
router.register(r'transactions', CoupleWalletTransactionViewSet, basename='couple-wallet-transactions')

urlpatterns = [
    # OTP endpoints (placed before router to avoid conflict)
    path('generate-otp/', GenerateCoupleWalletOTPView.as_view(), name='generate-couple-wallet-otp'),
    path('verify-otp/', VerifyCoupleWalletOTPView.as_view(), name='verify-couple-wallet-otp'),

    # Include router URLs
    path('', include(router.urls)),
]
