from django.db import models
from django.conf import settings
from django.db.models import Sum
from decimal import Decimal
from modeltranslation.translator import translator, TranslationOptions
from django.utils.translation import gettext_lazy as _


class DailySalary(models.Model):
    class PaymentType(models.TextChoices):
        CASH = 'CASH', 'Cash'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        DIGITAL_WALLET = 'DIGITAL_WALLET', 'Digital Wallet'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_salaries')
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=15, choices=PaymentType.choices, default=PaymentType.CASH)
    description = models.TextField(blank=True, help_text="Description of the work or source")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username}'s salary on {self.date}: {self.amount}"


class ExpenseTracking(models.Model):
    class Category(models.TextChoices):
        FOOD = 'FOOD', 'Food & Dining'
        TRANSPORT = 'TRANSPORT', 'Transportation'
        UTILITIES = 'UTILITIES', 'Utilities'
        HEALTHCARE = 'HEALTHCARE', 'Healthcare'
        ENTERTAINMENT = 'ENTERTAINMENT', 'Entertainment'
        CLOTHING = 'CLOTHING', 'Clothing'
        EDUCATION = 'EDUCATION', 'Education'
        HOUSEHOLD = 'HOUSEHOLD', 'Household'
        PERSONAL = 'PERSONAL', 'Personal Care'
        OTHER = 'OTHER', 'Other'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_expenses')
    date = models.DateField()
    category = models.CharField(max_length=15, choices=Category.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    is_essential = models.BooleanField(default=False, help_text="Mark as essential expense")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username}'s {self.category} expense on {self.date}: {self.amount}"


class DailySummary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_summaries')
    date = models.DateField(unique=True)
    total_salary = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_savings = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    essential_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    non_essential_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username}'s summary for {self.date}"

    def update_summary(self):
        """Update the summary based on current salary and expenses for the date."""
        # Calculate total salary for the date
        salary_sum = DailySalary.objects.filter(user=self.user, date=self.date).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # Calculate total expenses for the date
        expenses_sum = ExpenseTracking.objects.filter(user=self.user, date=self.date).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # Calculate essential and non-essential expenses
        essential_sum = ExpenseTracking.objects.filter(
            user=self.user, date=self.date, is_essential=True
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        non_essential_sum = expenses_sum - essential_sum

        # Update fields
        self.total_salary = salary_sum
        self.total_expenses = expenses_sum
        self.net_savings = salary_sum - expenses_sum
        self.essential_expenses = essential_sum
        self.non_essential_expenses = non_essential_sum
        self.save()


# Translation options for model fields
class DailySalaryTranslationOptions(TranslationOptions):
    fields = ('description',)

class ExpenseTrackingTranslationOptions(TranslationOptions):
    fields = ('description',)

# Translation options are now in translation.py

class UserProfile(models.Model):
    PERSONA_CHOICES = [
        ('INDIVIDUAL', 'Individual'),
        ('COUPLE', 'Couple'),
        ('PARENT', 'Parent'),
        ('STUDENT', 'Student'),
        ('DAILY_WAGE', 'Daily Wage Worker'),
        ('RETIREE', 'Retiree'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, verbose_name=_("Name"), help_text=_("Enter your name"))
    bio = models.TextField(blank=True, verbose_name=_("Bio"), help_text=_("Tell us about yourself"))
    location = models.CharField(max_length=100, blank=True, verbose_name=_("Location"), help_text=_("Where are you based?"))
    birth_date = models.DateField(null=True, blank=True, verbose_name=_("Birth Date"), help_text=_("When is your birthday?"))
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True, verbose_name=_("Profile Picture"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Phone"), help_text=_("Enter your phone number"))
    persona = models.CharField(max_length=20, choices=PERSONA_CHOICES, default='INDIVIDUAL', verbose_name=_("Account Type"), help_text=_("Select your account type"))

    def __str__(self):
        return f"{self.user.username}'s profile"
