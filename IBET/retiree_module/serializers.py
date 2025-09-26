from rest_framework import serializers
from .models import (
    IncomeSource, ExpenseCategory, Forecast, Alert,
    RetireeProfile, RetireeTransaction, RetireeAlert
)


class IncomeSourceSerializer(serializers.ModelSerializer):
    """Serializer for the IncomeSource model."""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = IncomeSource
        fields = [
            'id', 'user', 'user_username', 'source_type', 'amount', 'frequency',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_username', 'user']


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for the ExpenseCategory model."""
    user_username = serializers.CharField(source='user.username', read_only=True)
    variance = serializers.SerializerMethodField()

    class Meta:
        model = ExpenseCategory
        fields = [
            'id', 'user', 'user_username', 'category_name', 'budgeted_amount',
            'actual_spent', 'variance', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_username', 'variance', 'user']

    def get_variance(self, obj):
        return obj.get_variance()


class ForecastSerializer(serializers.ModelSerializer):
    """Serializer for the Forecast model."""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Forecast
        fields = [
            'id', 'user', 'user_username', 'forecast_type', 'period', 'predicted_amount',
            'confidence_level', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_username', 'user']


class AlertSerializer(serializers.ModelSerializer):
    """Serializer for the Alert model."""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Alert
        fields = [
            'id', 'user', 'user_username', 'alert_type', 'message', 'threshold',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user', 'user_username']


class RetireeProfileSerializer(serializers.ModelSerializer):
    """Serializer for the RetireeProfile model."""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RetireeProfile
        fields = [
            'id', 'user', 'user_username', 'pension_amount', 'savings', 'alert_threshold'
        ]
        read_only_fields = ['id', 'user', 'user_username']


class RetireeTransactionSerializer(serializers.ModelSerializer):
    """Serializer for the RetireeTransaction model."""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RetireeTransaction
        fields = [
            'id', 'user', 'user_username', 'amount', 'transaction_type',
            'transaction_date', 'description'
        ]
        read_only_fields = ['id', 'user', 'user_username']


class RetireeAlertSerializer(serializers.ModelSerializer):
    """Serializer for the RetireeAlert model."""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = RetireeAlert
        fields = ['id', 'user', 'user_username', 'triggered_on', 'message']
        read_only_fields = ['id', 'user', 'user_username', 'triggered_on']
