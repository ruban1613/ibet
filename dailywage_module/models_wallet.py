"""
Wallet functionality for Daily Wage Module.
Provides secure wallet operations with OTP protection and monitoring.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from modeltranslation.translator import translator, TranslationOptions


class DailyWageWallet(models.Model):
    """
    Secure wallet model for daily wage workers.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dailywage_wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    daily_earnings = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    weekly_target = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    monthly_goal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    emergency_reserve = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Threshold for low balance alerts")
    is_locked = models.BooleanField(default=False, help_text="Lock wallet for security reasons")
    last_transaction_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Daily Wage Wallet: {self.user.username} - Balance: {self.balance}"

    def add_daily_earnings(self, amount, description="Daily Earnings"):
        """Add daily earnings to wallet"""
        if amount <= 0:
            raise ValueError("Daily earnings amount must be positive")

        self.daily_earnings += amount
        self.balance += amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        DailyWageWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='DAILY_EARNINGS',
            description=description,
            balance_after=self.balance,
            daily_earnings_after=self.daily_earnings
        )
        return self.balance

    def withdraw(self, amount, description="Withdrawal", is_essential=False):
        """Securely withdraw money from wallet"""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        if self.is_locked:
            raise ValueError("Wallet is locked")

        # Check if withdrawal is for essential expenses
        if not is_essential and self._get_weekly_expenses() + amount > self.weekly_target:
            raise ValueError("Weekly spending limit exceeded")

        if self.balance < amount:
            raise ValueError("Insufficient balance")

        self.balance -= amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        DailyWageWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='WITHDRAWAL',
            description=description,
            balance_after=self.balance,
            is_essential_expense=is_essential
        )
        return self.balance

    def transfer_to_emergency(self, amount, description="Emergency Reserve Transfer"):
        """Transfer money to emergency reserve"""
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")

        if self.balance < amount:
            raise ValueError("Insufficient balance")

        self.balance -= amount
        self.emergency_reserve += amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        DailyWageWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='EMERGENCY_TRANSFER',
            description=description,
            balance_after=self.balance,
            emergency_reserve_after=self.emergency_reserve
        )
        return self.balance

    def _get_weekly_expenses(self):
        """Get total non-essential expenses for current week"""
        current_week_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(days=timezone.now().weekday())
        expenses = DailyWageWalletTransaction.objects.filter(
            wallet=self,
            transaction_type='WITHDRAWAL',
            is_essential_expense=False,
            created_at__gte=current_week_start
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        return expenses

    @property
    def available_balance(self):
        """Get available balance (excluding locked funds)"""
        return self.balance if not self.is_locked else Decimal('0.00')

    @property
    def weekly_progress(self):
        """Calculate weekly earnings progress"""
        if self.weekly_target > 0:
            return min((self.daily_earnings / self.weekly_target) * 100, 100)
        return 0

    @property
    def monthly_savings(self):
        """Calculate monthly savings"""
        return self.balance - self.emergency_reserve


class DailyWageWalletTransaction(models.Model):
    """
    Transaction history for daily wage wallets.
    """
    TRANSACTION_TYPES = [
        ('DAILY_EARNINGS', _('Daily Earnings')),
        ('WITHDRAWAL', _('Withdrawal')),
        ('EMERGENCY_TRANSFER', _('Emergency Reserve Transfer')),
        ('ESSENTIAL_EXPENSE', _('Essential Expense')),
        ('NON_ESSENTIAL_EXPENSE', _('Non-Essential Expense')),
    ]

    wallet = models.ForeignKey(DailyWageWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    transaction_type = models.CharField(max_length=25, choices=TRANSACTION_TYPES)
    description = models.TextField()
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    daily_earnings_after = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    emergency_reserve_after = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_essential_expense = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type}: {self.amount}"


class DailyWageWalletOTPRequest(models.Model):
    """
    OTP requests for daily wage wallet operations.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dailywage_otp_requests')
    operation_type = models.CharField(max_length=50, help_text="Type of operation requiring OTP")
    amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    otp_code = models.CharField(max_length=6)
    cache_key = models.CharField(max_length=100, default='', help_text="Cache key for OTP validation")
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.username} - {self.operation_type}"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def mark_as_used(self):
        self.is_used = True
        self.save()


# Translation options for model fields
class DailyWageWalletTransactionTranslationOptions(TranslationOptions):
    fields = ('description',)

# Translation options are now in translation.py
