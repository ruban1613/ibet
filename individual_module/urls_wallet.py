"""
URL configuration for Individual Module wallet functionality.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_wallet import (
    IndividualWalletViewSet, IndividualWalletTransactionViewSet,
    GenerateIndividualWalletOTPView, VerifyIndividualWalletOTPView
)

app_name = 'individual_wallet'

router = DefaultRouter()
router.register(r'', IndividualWalletViewSet, basename='individual-wallet')
router.register(r'transactions', IndividualWalletTransactionViewSet, basename='individual-wallet-transactions')

urlpatterns = [
    # OTP endpoints (placed before router to avoid conflict)
    path('generate-otp/', GenerateIndividualWalletOTPView.as_view(), name='generate-individual-wallet-otp'),
    path('verify-otp/', VerifyIndividualWalletOTPView.as_view(), name='verify-individual-wallet-otp'),

    # Include router URLs
    path('', include(router.urls)),
]
