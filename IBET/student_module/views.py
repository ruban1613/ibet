from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from .models import Budget, Category, Transaction, User, UserPersona, Reminder, ChatMessage, DailyLimit, OTPRequest
from django.db.models import Sum, Q
from django.utils import timezone
from .serializers import (
    BudgetSerializer, CategorySerializer, TransactionSerializer, UserSerializer, UserPersonaSerializer,
    ReminderSerializer, ChatMessageSerializer, DailyLimitSerializer, OTPRequestSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user).order_by('name')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OTPRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OTP requests to be viewed or edited.
    """
    serializer_class = OTPRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OTPGenerationThrottle]

    def get_queryset(self):
        return OTPRequest.objects.filter(student=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)


class VerifyOTPView(APIView):
    """
    API endpoint for student to verify OTP and receive extra funds from parent.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OTPVerificationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        from parent_module.models import ParentOTPRequest
        from parent_module.serializers import VerifyOTPSerializer
        from .models import Wallet

        serializer = VerifyOTPSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            otp_code = serializer.validated_data['otp_code']
            student_id = serializer.validated_data['student_id']

            # Find the OTP request
            try:
                otp_request = ParentOTPRequest.objects.get(
                    student_id=student_id,
                    otp_code=otp_code,
                    status='PENDING'
                )
            except ParentOTPRequest.DoesNotExist:
                return Response(
                    {'error': _('Invalid OTP or OTP request not found.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if OTP is expired
            if otp_request.is_expired():
                otp_request.mark_as_expired()
                return Response(
                    {'error': _('OTP has expired.')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify that the requesting user is the correct student
            if otp_request.student_id != request.user.id:
                return Response(
                    {'error': _('You are not authorized to use this OTP.')},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Add funds to student's wallet
            try:
                wallet = Wallet.objects.get(user=request.user)
                wallet.balance += otp_request.amount_requested
                wallet.save()
            except Wallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = Wallet.objects.create(
                    user=request.user,
                    balance=otp_request.amount_requested
                )

            # Mark OTP as used
            otp_request.mark_as_used()

            # Create transaction record
            Transaction.objects.create(
                user=request.user,
                amount=otp_request.amount_requested,
                transaction_type='INC',
                description=_(f'Extra funds from parent: {otp_request.reason}'),
                category=None  # Parent transfers don't need a category
            )

            return Response({
                'message': _('Successfully received funds from parent.'),
                'new_balance': wallet.balance,
                'reason': otp_request.reason
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BudgetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows budgets to be viewed or edited.
    It automatically filters budgets to only show the ones for the logged-in user.
    """
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user).order_by('-start_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """
        Returns a summary of the budget, including total spent and remaining amount.
        """
        budget = self.get_object()
        total_spent = Transaction.objects.filter(
            user=request.user,
            category=budget.category,
            transaction_date__range=[budget.start_date, budget.end_date],
            transaction_type='EXP'
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        remaining = budget.amount - total_spent

        return Response({
            'budget_amount': budget.amount,
            'total_spent': total_spent,
            'remaining': remaining,
            'category': budget.category.name,
        })


class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows transactions to be viewed or edited.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction_type', 'category']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-transaction_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SelectPersonaView(APIView):
    """
    An endpoint for the logged-in user to select their persona.
    Accepts a PATCH request with the 'persona' field, e.g. {"persona": "STUDENT"}
    """
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserPersonaSerializer(data=request.data)
        if serializer.is_valid():
            user.persona = serializer.validated_data['persona']
            user.save(update_fields=['persona'])
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Student-specific viewsets
class ReminderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reminders to be viewed or edited.
    """
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows chat messages to be viewed or edited.
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Show messages where user is sender or receiver
        return ChatMessage.objects.filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).order_by('-timestamp')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class DailyLimitViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows daily limits to be viewed or edited.
    """
    serializer_class = DailyLimitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DailyLimit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
