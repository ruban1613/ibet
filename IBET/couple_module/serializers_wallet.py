"""
Serializers for Couple Module wallet functionality.
"""
from rest_framework import serializers
from .models_wallet import CoupleWallet, CoupleWalletTransaction, CoupleWalletOTPRequest


class CoupleWalletSerializer(serializers.ModelSerializer):
    """Serializer for couple wallet model."""

    class Meta:
        model = CoupleWallet
        fields = [
            'id', 'balance', 'monthly_budget', 'emergency_fund', 'joint_goals',
            'is_locked', 'last_transaction_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_transaction_at']


class CoupleWalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for couple wallet transactions."""

    class Meta:
        model = CoupleWalletTransaction
        fields = [
            'id', 'amount', 'transaction_type', 'description', 'deposited_by',
            'withdrawn_by', 'balance_after', 'emergency_fund_after', 'joint_goals_after', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'balance_after', 'emergency_fund_after', 'joint_goals_after']


class CoupleWalletOTPRequestSerializer(serializers.ModelSerializer):
    """Serializer for couple wallet OTP requests."""

    class Meta:
        model = CoupleWalletOTPRequest
        fields = [
            'id', 'operation_type', 'amount', 'description', 'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at']


class CoupleWalletDepositSerializer(serializers.Serializer):
    """Serializer for couple wallet deposit operations."""
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False, default='Joint Deposit')


class CoupleWalletWithdrawalSerializer(serializers.Serializer):
    """Serializer for couple wallet withdrawal operations."""
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False, default='Joint Withdrawal')


class CoupleWalletEmergencyTransferSerializer(serializers.Serializer):
    """Serializer for couple wallet emergency fund transfers."""
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0.01)
    description = serializers.CharField(max_length=255, required=False, default='Emergency Fund Transfer')


class CoupleWalletGoalTransferSerializer(serializers.Serializer):
    """Serializer for couple wallet joint goal transfers."""
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0.01)
    goal_name = serializers.CharField(max_length=100, required=False, default='Joint Goal')
    description = serializers.CharField(max_length=255, required=False, default='Joint Goal Transfer')


class GenerateCoupleWalletOTPSerializer(serializers.Serializer):
    """Serializer for generating OTP for couple wallet operations."""
    operation_type = serializers.ChoiceField(choices=[
        ('deposit', 'Joint Deposit'),
        ('withdrawal', 'Joint Withdrawal'),
        ('emergency_transfer', 'Emergency Fund Transfer'),
        ('goal_transfer', 'Joint Goal Transfer'),
    ])
    amount = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    description = serializers.CharField(max_length=255, required=False)
    goal_name = serializers.CharField(max_length=100, required=False)


class VerifyCoupleWalletOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP for couple wallet operations."""
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_request_id = serializers.IntegerField()


class CoupleWalletMonthlySummarySerializer(serializers.Serializer):
    """Serializer for couple wallet monthly summary."""
    total_deposits = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_withdrawals = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_transfers = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_count = serializers.IntegerField()
    monthly_budget = serializers.DecimalField(max_digits=10, decimal_places=2)
    budget_utilization = serializers.DecimalField(max_digits=5, decimal_places=2)
