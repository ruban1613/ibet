"""
Serializers for Student Module wallet functionality.
"""
from rest_framework import serializers
from .models import Wallet, OTPRequest, ParentStudentLink
from decimal import Decimal


class StudentWalletSerializer(serializers.ModelSerializer):
    """Serializer for student wallet model."""

    class Meta:
        model = Wallet
        fields = [
            'id', 'balance', 'is_locked', 'last_transaction_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_transaction_at']


class StudentWalletDepositSerializer(serializers.Serializer):
    """Serializer for wallet deposit operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default='Deposit')


class StudentWalletWithdrawalSerializer(serializers.Serializer):
    """Serializer for wallet withdrawal operations."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default='Withdrawal')


class StudentWalletParentApprovalSerializer(serializers.Serializer):
    """Serializer for parent approval requests."""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, required=False, default='Transaction request')


class GenerateStudentWalletOTPSerializer(serializers.Serializer):
    """Serializer for generating OTP for wallet operations."""
    operation_type = serializers.ChoiceField(choices=[
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('parent_approval', 'Parent Approval Request'),
    ])
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    description = serializers.CharField(max_length=255, required=False)


class VerifyStudentWalletOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP for wallet operations."""
    otp_code = serializers.CharField(max_length=6, min_length=6)
    otp_request_id = serializers.IntegerField()


class StudentOTPRequestSerializer(serializers.ModelSerializer):
    """Serializer for student OTP requests."""

    class Meta:
        model = OTPRequest
        fields = [
            'id', 'student', 'parent', 'amount_requested', 'is_used',
            'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'expires_at', 'is_used']
