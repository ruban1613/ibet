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
router.register(r'wallet', DailyWageWalletViewSet, basename='dailywage-wallet')
router.register(r'transactions', DailyWageWalletTransactionViewSet, basename='dailywage-wallet-transactions')

urlpatterns = [
    # Balance endpoint (placed before router to avoid conflict)
    path('balance/', DailyWageWalletViewSet.as_view({'get': 'balance'}), name='dailywage-wallet-balance'),

    # Additional endpoints for weekly and monthly summaries (placed before router to avoid conflict)
    path('weekly-summary/', DailyWageWalletViewSet.as_view({'get': 'weekly_summary'}), name='dailywage-wallet-weekly-summary'),
    path('monthly-summary/', DailyWageWalletViewSet.as_view({'get': 'monthly_summary'}), name='dailywage-wallet-monthly-summary'),

    # OTP endpoints (placed before router to avoid conflict)
    path('generate-otp/', GenerateDailyWageWalletOTPView.as_view(), name='generate-dailywage-wallet-otp'),
    path('verify-otp/', VerifyDailyWageWalletOTPView.as_view(), name='verify-dailywage-wallet-otp'),

    # Include router URLs
    path('', include(router.urls)),
]
