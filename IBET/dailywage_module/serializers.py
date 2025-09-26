from rest_framework import serializers
from .models import DailySalary, ExpenseTracking, DailySummary


class DailySalarySerializer(serializers.ModelSerializer):
    """Serializer for the DailySalary model."""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = DailySalary
        fields = [
            'id', 'user', 'user_username', 'date', 'amount', 'payment_type',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_username', 'user']


class ExpenseTrackingSerializer(serializers.ModelSerializer):
    """Serializer for the ExpenseTracking model."""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ExpenseTracking
        fields = [
            'id', 'user', 'user_username', 'date', 'category', 'amount',
            'description', 'is_essential', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_username', 'user']


class DailySummarySerializer(serializers.ModelSerializer):
    """Serializer for the DailySummary model."""
    user_username = serializers.CharField(source='user.username', read_only=True)
    total_salary = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_expenses = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    net_savings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    essential_expenses = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    non_essential_expenses = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = DailySummary
        fields = [
            'id', 'user', 'user_username', 'date', 'total_salary', 'total_expenses',
            'net_savings', 'essential_expenses', 'non_essential_expenses',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'user_username', 'user',
            'total_salary', 'total_expenses', 'net_savings',
            'essential_expenses', 'non_essential_expenses'
        ]
