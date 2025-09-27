from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from modeltranslation.translator import translator, TranslationOptions

User = get_user_model()


class IncomeSource(models.Model):
    """
    Model to track different income sources for individuals
    """
    INCOME_TYPES = [
        ('SALARY', 'Salary'),
        ('FREELANCE', 'Freelance'),
        ('BUSINESS', 'Business'),
        ('RENTAL', 'Rental Income'),
        ('INVESTMENT', 'Investment'),
        ('OTHER', 'Other'),
    ]

    FREQUENCY_CHOICES = [
        ('WEEKLY', 'Weekly'),
        ('BIWEEKLY', 'Bi-weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='income_sources')
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    income_type = models.CharField(max_length=20, choices=INCOME_TYPES, default='SALARY')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='MONTHLY')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.amount})"


class EmergencyFund(models.Model):
    """
    Model to track emergency funds for individuals
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='emergency_fund')
    target_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Target emergency fund amount")
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    monthly_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    target_months = models.PositiveIntegerField(help_text="Number of months the fund should cover", default=6)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def progress_percentage(self):
        """Calculate progress towards emergency fund goal"""
        if self.target_amount > 0:
            return min((self.current_amount / self.target_amount) * 100, 100)
        return 0

    @property
    def months_covered(self):
        """Calculate how many months the current fund can cover"""
        if self.monthly_contribution > 0:
            return self.current_amount / self.monthly_contribution
        return 0

    def __str__(self):
        return f"{self.user.username} Emergency Fund - {self.current_amount}/{self.target_amount}"


class IndividualDashboard(models.Model):
    """
    Dashboard model for individual users to track their financial overview
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='individual_dashboard')
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    savings_goal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    current_savings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def remaining_budget(self):
        """Calculate remaining budget for the month"""
        return self.monthly_budget - self.total_expenses

    @property
    def savings_progress(self):
        """Calculate savings goal progress"""
        if self.savings_goal > 0:
            return min((self.current_savings / self.savings_goal) * 100, 100)
        return 0

    def __str__(self):
        return f"{self.user.username} Dashboard"


class ExpenseAlert(models.Model):
    """
    Model for expense alerts and notifications
    """
    ALERT_TYPES = [
        ('BUDGET_50', '50% Budget Used'),
        ('BUDGET_75', '75% Budget Used'),
        ('BUDGET_100', '100% Budget Used'),
        ('EMERGENCY_LOW', 'Emergency Fund Low'),
        ('SAVINGS_GOAL', 'Savings Goal Reminder'),
        ('CUSTOM', 'Custom Alert'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    threshold_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def mark_as_read(self):
        """Mark alert as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class FinancialGoal(models.Model):
    """
    Model for tracking financial goals
    """
    GOAL_TYPES = [
        ('SHORT_TERM', 'Short Term (1-6 months)'),
        ('MEDIUM_TERM', 'Medium Term (6-18 months)'),
        ('LONG_TERM', 'Long Term (1+ years)'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('PAUSED', 'Paused'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='financial_goals')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES, default='SHORT_TERM')
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def progress_percentage(self):
        """Calculate progress towards goal"""
        if self.target_amount > 0:
            return min((self.current_amount / self.target_amount) * 100, 100)
        return 0

    @property
    def days_remaining(self):
        """Calculate days remaining to reach target date"""
        if self.target_date:
            return (self.target_date - timezone.now().date()).days
        return 0

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.progress_percentage:.1f}%)"


# Translation options for model fields
class IncomeSourceTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class ExpenseAlertTranslationOptions(TranslationOptions):
    fields = ('title', 'message')

class FinancialGoalTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

# Translation options are now in translation.py
