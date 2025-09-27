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
router.register(r'wallet/transactions', DailyWageWalletTransactionViewSet, basename='dailywage-wallet-transactions')

urlpatterns = [
    path('', include(router.urls)),
    path('generate-otp/', GenerateDailyWageWalletOTPView.as_view(), name='generate-dailywage-wallet-otp'),
    path('verify-otp/', VerifyDailyWageWalletOTPView.as_view(), name='verify-dailywage-wallet-otp'),
]
