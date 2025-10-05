"""
Serializers for Daily Wage Module wallet functionality.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models_wallet import DailyWageWallet, DailyWageWalletTransaction, DailyWageWalletOTPRequest


class DailyWageWalletSerializer(serializers.ModelSerializer):
    """Serializer for daily wage wallet model."""

    class Meta:
        model = DailyWageWallet
        fields = [
            'id', 'balance', 'daily_earnings', 'weekly_target', 'monthly_goal',
            'emergency_reserve', 'alert_threshold', 'is_locked', 'last_transaction_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_transaction_at']


class DailyWageWalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for daily wage wallet transactions."""

    class Meta:
        model = DailyWageWalletTransaction
        fields = [
            'id', 'amount', 'transaction_type', 'description', 'balance_after',
            'daily_earnings_after', 'emergency_reserve_after', 'is_essential_expense', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'balance_after', 'daily_earnings_after', 'emergency_reserve_after']


class DailyWageWalletOTPRequestSerializer(serializers.ModelSerializer):
    """Serializer for daily wage wallet OTP requests."""

    class Meta:
        model = DailyWageWalletOTPRequest
        fields = [
            'id', 'operation_type', 'amount', 'description', 'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at']


class DailyWageWalletEarningsSerializer(serializers.Serializer):
    """Serializer for adding daily earnings."""
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False, default='Daily Earnings')


class DailyWageWalletWithdrawalSerializer(serializers.Serializer):
    """Serializer for wallet withdrawal operations."""
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False, default='Withdrawal')
    is_essential = serializers.BooleanField(default=False, required=False)


class DailyWageWalletTransferSerializer(serializers.Serializer):
    """Serializer for wallet transfer to emergency reserve."""
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False, default='Emergency Reserve Transfer')


class GenerateDailyWageWalletOTPSerializer(serializers.Serializer):
    """Serializer for generating OTP for wallet operations."""
    operation_type = serializers.ChoiceField(choices=[
        ('add_earnings', _('Add Daily Earnings')),
        ('withdrawal', _('Withdrawal')),
        ('emergency_transfer', _('Emergency Reserve Transfer')),
    ])
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    description = serializers.CharField(max_length=255, required=False)


class VerifyDailyWageWalletOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP for wallet operations."""
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_request_id = serializers.IntegerField()
