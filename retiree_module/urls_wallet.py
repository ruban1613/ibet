"""
URL configuration for Retiree Module wallet functionality.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet import (
    RetireeWalletViewSet, RetireeWalletTransactionViewSet,
    GenerateRetireeWalletOTPView, VerifyRetireeWalletOTPView
)

app_name = 'retiree_wallet'

router = DefaultRouter()
router.register(r'wallet', RetireeWalletViewSet, basename='retiree-wallet')
router.register(r'transactions', RetireeWalletTransactionViewSet, basename='retiree-wallet-transactions')

urlpatterns = [
    path('generate-otp/', GenerateRetireeWalletOTPView.as_view(), name='generate-retiree-wallet-otp'),
    path('verify-otp/', VerifyRetireeWalletOTPView.as_view(), name='verify-retiree-wallet-otp'),
    path('', include(router.urls)),
    # Explicit balance endpoint for URL reversal
    path('wallet/balance/', RetireeWalletViewSet.as_view({'get': 'balance'}), name='retiree-wallet-balance'),
]
