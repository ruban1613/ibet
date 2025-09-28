"""
URL configuration for Daily Wage Module wallet functionality.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet import (
    DailyWageWalletViewSet, DailyWageWalletTransactionViewSet,
    GenerateDailyWageWalletOTPView, VerifyDailyWageWalletOTPView
)

app_name = 'dailywage_wallet'

router = DefaultRouter()
router.register(r'', DailyWageWalletViewSet, basename='dailywage-wallet')
router.register(r'transactions', DailyWageWalletTransactionViewSet, basename='dailywage-wallet-transactions')

urlpatterns = [
    # OTP endpoints (placed before router to avoid conflict)
    path('generate-otp/', GenerateDailyWageWalletOTPView.as_view(), name='generate-dailywage-wallet-otp'),
    path('verify-otp/', VerifyDailyWageWalletOTPView.as_view(), name='verify-dailywage-wallet-otp'),

    # Include router URLs
    path('', include(router.urls)),
]
