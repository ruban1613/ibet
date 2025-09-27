from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import ParentDashboard, AlertSettings, StudentMonitoring, ParentAlert, ParentOTPRequest
from student_module.models import ParentStudentLink, Transaction, Wallet, DailyLimit
from django.db.models import Sum


class ParentDashboardSerializer(serializers.ModelSerializer):
    """Serializer for the ParentDashboard model."""
    total_student_spending = serializers.SerializerMethodField()
    linked_students_count = serializers.SerializerMethodField()

    class Meta:
        model = ParentDashboard
        fields = [
            'id', 'total_students', 'total_alerts_sent', 'last_accessed',
            'total_student_spending', 'linked_students_count'
        ]
        read_only_fields = ['id', 'last_accessed']

    def get_total_student_spending(self, obj):
        return obj.get_total_student_spending()

    def get_linked_students_count(self, obj):
        return ParentStudentLink.objects.filter(parent=obj.parent).count()


class AlertSettingsSerializer(serializers.ModelSerializer):
    """Serializer for the AlertSettings model."""
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = AlertSettings
        fields = [
            'id', 'parent', 'student', 'parent_username', 'student_username',
            'alert_type', 'is_enabled', 'email_notification', 'sms_notification', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'parent_username', 'student_username']


class StudentMonitoringSerializer(serializers.ModelSerializer):
    """Serializer for the StudentMonitoring model."""
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = StudentMonitoring
        fields = [
            'id', 'parent', 'student', 'parent_username', 'student_username',
            'accessed_at', 'wallet_accessed', 'otp_generated', 'notes'
        ]
        read_only_fields = ['id', 'accessed_at', 'parent_username', 'student_username']


class ParentAlertSerializer(serializers.ModelSerializer):
    """Serializer for the ParentAlert model."""
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = ParentAlert
        fields = [
            'id', 'parent', 'student', 'parent_username', 'student_username',
            'alert_type', 'message', 'status', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'parent_username', 'student_username']


class StudentWalletAccessSerializer(serializers.Serializer):
    """Serializer for parent accessing student's wallet."""
    student_id = serializers.IntegerField()
    amount_needed = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(max_length=255)

    def validate_student_id(self, value):
        request = self.context.get('request')
        if not ParentStudentLink.objects.filter(parent=request.user, student_id=value).exists():
            raise serializers.ValidationError("You are not linked to this student.")
        return value


class StudentOverviewSerializer(serializers.Serializer):
    """Serializer for parent viewing student's overview."""
    student_id = serializers.IntegerField()
    wallet_balance = serializers.SerializerMethodField()
    daily_limit = serializers.SerializerMethodField()
    current_daily_spent = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()

    def get_wallet_balance(self, obj):
        try:
            wallet = Wallet.objects.get(user_id=obj['student_id'])
            return wallet.balance
        except Wallet.DoesNotExist:
            return 0.00

    def get_daily_limit(self, obj):
        try:
            daily_limit = DailyLimit.objects.get(user_id=obj['student_id'])
            return {
                'monthly_budget': daily_limit.monthly_budget,
                'daily_limit_amount': daily_limit.daily_limit_amount,
                'current_daily_spent': daily_limit.current_daily_spent
            }
        except DailyLimit.DoesNotExist:
            return None

    def get_current_daily_spent(self, obj):
        # Calculate current day's spending
        from django.utils import timezone
        today = timezone.now().date()
        return Transaction.objects.filter(
            user_id=obj['student_id'],
            transaction_date=today,
            transaction_type='EXP'
        ).aggregate(total=Sum('amount'))['total'] or 0.00

    def get_recent_transactions(self, obj):
        transactions = Transaction.objects.filter(
            user_id=obj['student_id']
        ).order_by('-transaction_date')[:5]
        return [{
            'id': t.id,
            'amount': t.amount,
            'transaction_type': t.transaction_type,
            'description': t.description,
            'date': t.transaction_date
        } for t in transactions]


class ParentOTPRequestSerializer(serializers.ModelSerializer):
    """Serializer for the ParentOTPRequest model."""
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    student_username = serializers.CharField(source='student.username', read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = ParentOTPRequest
        fields = [
            'id', 'parent', 'student', 'parent_username', 'student_username',
            'otp_code', 'amount_requested', 'reason', 'status', 'created_at',
            'expires_at', 'used_at', 'is_expired'
        ]
        read_only_fields = [
            'id', 'otp_code', 'created_at', 'expires_at', 'used_at',
            'parent_username', 'student_username', 'is_expired'
        ]

    def get_is_expired(self, obj):
        return obj.is_expired()


class GenerateOTPSerializer(serializers.Serializer):
    """Serializer for generating OTP for student wallet access."""
    student_id = serializers.IntegerField()
    amount_requested = serializers.DecimalField(max_digits=10, decimal_places=2)
    reason = serializers.CharField(max_length=255)

    def validate_student_id(self, value):
        request = self.context.get('request')
        if not ParentStudentLink.objects.filter(parent=request.user, student_id=value).exists():
            raise serializers.ValidationError("You are not linked to this student.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP."""
    otp_code = serializers.CharField(max_length=6)
    student_id = serializers.IntegerField()

    def validate_otp_code(self, value):
        if len(value) != 6 or not value.isdigit():
            raise serializers.ValidationError("OTP must be 6 digits.")
        return value

    def validate_student_id(self, value):
        request = self.context.get('request')
        if not ParentStudentLink.objects.filter(parent=request.user, student_id=value).exists():
            raise serializers.ValidationError("You are not linked to this student.")
        return value
