"""
Serializers for Retiree Module wallet functionality.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models_wallet import RetireeWallet, RetireeWalletTransaction, RetireeWalletOTPRequest
from decimal import Decimal


class RetireeWalletSerializer(serializers.ModelSerializer):
    """Serializer for retiree wallet model."""

    class Meta:
        model = RetireeWallet
        fields = [
            'id', 'balance', 'pension_balance', 'emergency_fund', 'monthly_expense_limit',
            'is_locked', 'last_transaction_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_transaction_at']


class RetireeWalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for retiree wallet transactions."""

    class Meta:
        model = RetireeWalletTransaction
        fields = [
            'id', 'amount', 'transaction_type', 'description', 'balance_after',
            'pension_balance_after', 'emergency_balance_after', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'balance_after', 'pension_balance_after', 'emergency_balance_after']


class RetireeWalletOTPRequestSerializer(serializers.ModelSerializer):
    """Serializer for retiree wallet OTP requests."""

    class Meta:
        model = RetireeWalletOTPRequest
        fields = [
            'id', 'operation_type', 'amount', 'description', 'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at']


class RetireeWalletDepositSerializer(serializers.Serializer):
    """Serializer for wallet deposit operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default=_('Deposit'))


class RetireeWalletWithdrawalSerializer(serializers.Serializer):
    """Serializer for wallet withdrawal operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default=_('Withdrawal'))
    use_pension_fund = serializers.BooleanField(default=False, required=False)


class GenerateRetireeWalletOTPSerializer(serializers.Serializer):
    """Serializer for generating OTP for wallet operations."""
    operation_type = serializers.ChoiceField(choices=[
        ('pension_deposit', _('Pension Deposit')),
        ('emergency_deposit', _('Emergency Fund Deposit')),
        ('withdrawal', _('Withdrawal')),
    ])
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    description = serializers.CharField(max_length=255, required=False)


class VerifyRetireeWalletOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP for wallet operations."""
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_request_id = serializers.IntegerField()
