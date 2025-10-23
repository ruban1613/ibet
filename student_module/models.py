# c:\Users\Hp\Documents\budget\IBET\student_module\models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from modeltranslation.translator import translator, TranslationOptions

# Step 1: Define User Personas using a TextChoices class for clarity.
class UserPersona(models.TextChoices):
    STUDENT = 'STUDENT', 'Student'
    PARENT = 'PARENT', 'Parent'
    INDIVIDUAL = 'INDIVIDUAL', 'Individual'
    COUPLE = 'COUPLE', 'Couple'
    RETIREE = 'RETIREE', 'Retiree'
    DAILY_WAGER = 'DAILY_WAGER', 'Daily Wager'

# Step 2: Enhance the User model to include the persona.
class User(AbstractUser):
    # This field is the core of your multi-persona system.
    persona = models.CharField(
        max_length=20,
        choices=UserPersona.choices,
        null=True, # Allow null until the user selects their persona after registration.
        blank=True
    )
    # You can add other common fields here if needed.

# Step 3: Create a Wallet model. This is a central concept for many personas.
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_transaction_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet: {self.balance}"

# Step 4: Model for the Parent-Student relationship.
class ParentStudentLink(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='linked_students')
    student = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='linked_parent')

    def __str__(self):
        return f"Parent: {self.parent.username} -> Student: {self.student.username}"

# Step 5: Model for the "Couples" spending approval workflow.
class SpendingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    # A shared wallet would be ideal here, but for simplicity, we can link to the requester's partner.
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_requests')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

# Your existing models are great. We just need to ensure they link to the User.
class Category(models.Model):
    # Make categories user-specific so one user doesn't see another's categories.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name=_("Name"), help_text=_("Enter your name"))

    def __str__(self):
        return self.name

class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.user.username}'s budget for {self.category.name}"

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = 'INC', 'Income'
        EXPENSE = 'EXP', 'Expense'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=3, choices=TransactionType.choices)
    transaction_date = models.DateField()
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.user.username}"

# New models for student features
class Reminder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, null=True, blank=True)
    alert_percentage = models.IntegerField(choices=[(50, '50%'), (70, '70%'), (100, '100%')], default=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reminder for {self.user.username} at {self.alert_percentage}%"

class ChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

class DailyLimit(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    daily_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Daily limit for {self.user.username}: {self.daily_amount}"

class OTPRequest(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_otp_requests')
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parent_otp_responses')
    otp_code = models.CharField(max_length=6)
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.student.username} from {self.parent.username}"


# Translation options are now in translation.py



