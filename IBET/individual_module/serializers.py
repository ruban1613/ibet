from rest_framework import serializers
from .models import (
    IncomeSource, EmergencyFund, IndividualDashboard,
    ExpenseAlert, FinancialGoal
)
from student_module.models import Wallet, Transaction


class IncomeSourceSerializer(serializers.ModelSerializer):
    """
    Serializer for IncomeSource model
    """
    class Meta:
        model = IncomeSource
        fields = [
            'id', 'name', 'income_type', 'amount', 'frequency',
            'description', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmergencyFundSerializer(serializers.ModelSerializer):
    """
    Serializer for EmergencyFund model
    """
    progress_percentage = serializers.ReadOnlyField()
    months_covered = serializers.ReadOnlyField()

    class Meta:
        model = EmergencyFund
        fields = [
            'id', 'target_amount', 'current_amount', 'monthly_contribution',
            'target_months', 'progress_percentage', 'months_covered',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class IndividualDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer for IndividualDashboard model
    """
    remaining_budget = serializers.ReadOnlyField()
    savings_progress = serializers.ReadOnlyField()

    class Meta:
        model = IndividualDashboard
        fields = [
            'id', 'total_income', 'total_expenses', 'monthly_budget',
            'savings_goal', 'current_savings', 'remaining_budget',
            'savings_progress', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']


class ExpenseAlertSerializer(serializers.ModelSerializer):
    """
    Serializer for ExpenseAlert model
    """
    class Meta:
        model = ExpenseAlert
        fields = [
            'id', 'alert_type', 'title', 'message', 'threshold_amount',
            'is_active', 'is_read', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']


class FinancialGoalSerializer(serializers.ModelSerializer):
    """
    Serializer for FinancialGoal model
    """
    progress_percentage = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()

    class Meta:
        model = FinancialGoal
        fields = [
            'id', 'name', 'description', 'goal_type', 'target_amount',
            'current_amount', 'target_date', 'status', 'progress_percentage',
            'days_remaining', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer for Wallet model (from student_module)
    """
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model (from student_module)
    """
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'amount', 'transaction_type', 'description',
            'transaction_date', 'category', 'category_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class IndividualOverviewSerializer(serializers.Serializer):
    """
    Serializer for individual financial overview
    """
    wallet_balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    monthly_expenses = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    emergency_fund_progress = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    active_goals_count = serializers.IntegerField(read_only=True)
    unread_alerts_count = serializers.IntegerField(read_only=True)
    recent_transactions = TransactionSerializer(many=True, read_only=True)
