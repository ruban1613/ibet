"""
Wallet functionality for Retiree Module.
Provides secure wallet operations with OTP protection and monitoring.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from modeltranslation.translator import translator, TranslationOptions


class RetireeWallet(models.Model):
    """
    Secure wallet model for retiree users.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retiree_wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    pension_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Dedicated pension funds")
    emergency_fund = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Emergency fund balance")
    monthly_expense_limit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_locked = models.BooleanField(default=False, help_text="Lock wallet for security reasons")
    last_transaction_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Retiree Wallet: {self.user.username} - Balance: {self.balance}"

    def deposit_pension(self, amount, description="Pension Deposit"):
        """Deposit pension money to dedicated pension balance"""
        if amount <= 0:
            raise ValueError("Pension deposit amount must be positive")

        self.pension_balance += amount
        self.balance += amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        RetireeWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='PENSION_DEPOSIT',
            description=description,
            balance_after=self.balance,
            pension_balance_after=self.pension_balance
        )
        return self.balance

    def deposit_emergency(self, amount, description="Emergency Fund Deposit"):
        """Deposit money to emergency fund"""
        if amount <= 0:
            raise ValueError("Emergency fund deposit amount must be positive")

        self.emergency_fund += amount
        self.balance += amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        RetireeWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='EMERGENCY_DEPOSIT',
            description=description,
            balance_after=self.balance,
            emergency_balance_after=self.emergency_fund
        )
        return self.balance

    def withdraw(self, amount, description="Withdrawal", use_pension_fund=False):
        """Securely withdraw money from wallet"""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")

        if self.is_locked:
            raise ValueError("Wallet is locked")

        # Check monthly expense limit
        if not use_pension_fund and self._get_monthly_expenses() + amount > self.monthly_expense_limit:
            raise ValueError("Monthly expense limit exceeded")

        if self.balance < amount:
            raise ValueError("Insufficient balance")

        self.balance -= amount
        self.last_transaction_at = timezone.now()
        self.save()

        # Create transaction record
        RetireeWalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='WITHDRAWAL',
            description=description,
            balance_after=self.balance
        )
        return self.balance

    def _get_monthly_expenses(self):
        """Get total expenses for current month"""
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        expenses = RetireeWalletTransaction.objects.filter(
            wallet=self,
            transaction_type='WITHDRAWAL',
            created_at__gte=current_month
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        return expenses

    @property
    def available_balance(self):
        """Get available balance (excluding locked funds)"""
        return self.balance if not self.is_locked else Decimal('0.00')

    @property
    def total_funds(self):
        """Get total of all fund types"""
        return self.balance + self.pension_balance + self.emergency_fund


class RetireeWalletTransaction(models.Model):
    """
    Transaction history for retiree wallets.
    """
    TRANSACTION_TYPES = [
        ('PENSION_DEPOSIT', _('Pension Deposit')),
        ('EMERGENCY_DEPOSIT', _('Emergency Fund Deposit')),
        ('WITHDRAWAL', _('Withdrawal')),
        ('TRANSFER', _('Transfer')),
        ('FORECAST_EXPENSE', _('Forecast Expense')),
    ]

    wallet = models.ForeignKey(RetireeWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField()
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    pension_balance_after = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    emergency_balance_after = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type}: {self.amount}"


class RetireeWalletOTPRequest(models.Model):
    """
    OTP requests for retiree wallet operations.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='retiree_otp_requests')
    operation_type = models.CharField(max_length=50, help_text="Type of operation requiring OTP")
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    otp_code = models.CharField(max_length=6)
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
class RetireeWalletTransactionTranslationOptions(TranslationOptions):
    fields = ('description',)

# Translation options are now in translation.py
