from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from .models import (
    IncomeSource, ExpenseCategory, Forecast, Alert,
    RetireeProfile, RetireeTransaction, RetireeAlert
)
from .serializers import (
    IncomeSourceSerializer, ExpenseCategorySerializer, ForecastSerializer, AlertSerializer,
    RetireeProfileSerializer, RetireeTransactionSerializer, RetireeAlertSerializer
)
class IncomeSourceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows income sources to be viewed or edited.
    """
    queryset = IncomeSource.objects.all()
    serializer_class = IncomeSourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows expense categories to be viewed or edited.
    """
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ForecastViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows forecasts to be viewed or edited.
    """
    queryset = Forecast.objects.all()
    serializer_class = ForecastSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate_forecast(self, request):
        """Generate a forecast based on income and expenses."""
        user = request.user
        forecast_type = request.data.get('forecast_type', 'BUDGET')
        period = request.data.get('period', 'MONTHLY')

        # Calculate total income
        total_income = IncomeSource.objects.filter(user=user).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # Calculate total expenses
        total_expenses = ExpenseCategory.objects.filter(user=user).aggregate(
            total=Sum('budgeted_amount')
        )['total'] or Decimal('0.00')

        # Simple forecast calculation
        if forecast_type == 'BUDGET':
            predicted_amount = total_income - total_expenses
        else:
            predicted_amount = total_expenses

        forecast = Forecast.objects.create(
            user=user,
            forecast_type=forecast_type,
            period=period,
            predicted_amount=predicted_amount,
            confidence_level=75,
            notes=f"Auto-generated forecast based on current data"
        )

        serializer = self.get_serializer(forecast)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def reports(self, request):
        """Get financial reports for the retiree."""
        user = request.user

        total_income = IncomeSource.objects.filter(user=user).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        total_budgeted = ExpenseCategory.objects.filter(user=user).aggregate(
            total=Sum('budgeted_amount')
        )['total'] or Decimal('0.00')

        total_actual = ExpenseCategory.objects.filter(user=user).aggregate(
            total=Sum('actual_spent')
        )['total'] or Decimal('0.00')

        variance = total_budgeted - total_actual

        report = {
            'total_income': total_income,
            'total_budgeted_expenses': total_budgeted,
            'total_actual_expenses': total_actual,
            'budget_variance': variance,
            'forecasts_count': Forecast.objects.filter(user=user).count(),
            'alerts_count': Alert.objects.filter(user=user, is_active=True).count()
        }

        return Response(report)


class AlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows alerts to be viewed or edited.
    """
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RetireeProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows retiree profiles to be viewed or edited.
    """
    queryset = RetireeProfile.objects.all()
    serializer_class = RetireeProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RetireeTransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows retiree transactions to be viewed or edited.
    """
    queryset = RetireeTransaction.objects.all()
    serializer_class = RetireeTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RetireeAlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows retiree alerts to be viewed or edited.
    """
    queryset = RetireeAlert.objects.all()
    serializer_class = RetireeAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
