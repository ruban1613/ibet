from django.db import models
from django.conf import settings
from django.db.models import Sum
from decimal import Decimal
from modeltranslation.translator import translator, TranslationOptions
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def get_today():
    """Helper function to get today's date."""
    return timezone.now().date()


class IncomeSource(models.Model):
    class Frequency(models.TextChoices):
        MONTHLY = 'MONTHLY', 'Monthly'
        QUARTERLY = 'QUARTERLY', 'Quarterly'
        YEARLY = 'YEARLY', 'Yearly'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retiree_income_sources')
    source_type = models.CharField(max_length=100, help_text="e.g., Pension, Investment, Rental")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.MONTHLY)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.source_type} Income"


class ExpenseCategory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expense_categories')
    category_name = models.CharField(max_length=100)
    budgeted_amount = models.DecimalField(max_digits=10, decimal_places=2)
    actual_spent = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.category_name} Expense"

    def get_variance(self):
        return self.budgeted_amount - self.actual_spent


class Forecast(models.Model):
    class ForecastType(models.TextChoices):
        BUDGET = 'BUDGET', 'Budget Forecast'
        EXPENSE = 'EXPENSE', 'Expense Forecast'

    class Period(models.TextChoices):
        MONTHLY = 'MONTHLY', 'Monthly'
        QUARTERLY = 'QUARTERLY', 'Quarterly'
        YEARLY = 'YEARLY', 'Yearly'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forecasts')
    forecast_type = models.CharField(max_length=10, choices=ForecastType.choices)
    period = models.CharField(max_length=10, choices=Period.choices)
    predicted_amount = models.DecimalField(max_digits=10, decimal_places=2)
    confidence_level = models.PositiveIntegerField(default=80, help_text="Confidence percentage (0-100)")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.forecast_type} Forecast for {self.period}"


class Alert(models.Model):
    class AlertType(models.TextChoices):
        BUDGET = 'BUDGET', 'Budget Alert'
        EXPENSE = 'EXPENSE', 'Expense Alert'
        FORECAST = 'FORECAST', 'Forecast Alert'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retiree_alerts')
    alert_type = models.CharField(max_length=10, choices=AlertType.choices)
    message = models.TextField()
    threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.alert_type} Alert"


class RetireeProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retiree_profile')
    pension_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    savings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)  # Example threshold

    def __str__(self):
        return f"Retiree Profile: {self.user.username}"


class RetireeTransaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = 'INC', 'Income'
        EXPENSE = 'EXP', 'Expense'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=3, choices=TransactionType.choices)
    transaction_date = models.DateField(default=get_today)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.user.username}"


class RetireeAlert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    triggered_on = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255)

    def __str__(self):
        return f"Alert for {self.user.username} at {self.triggered_on}"


# Translation options for model fields
class IncomeSourceTranslationOptions(TranslationOptions):
    fields = ('source_type', 'description')

class ExpenseCategoryTranslationOptions(TranslationOptions):
    fields = ('category_name', 'description')

class ForecastTranslationOptions(TranslationOptions):
    fields = ('notes',)

class AlertTranslationOptions(TranslationOptions):
    fields = ('message',)

# Translation options are now in translation.py
