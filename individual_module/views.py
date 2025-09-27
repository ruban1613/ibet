from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
from decimal import Decimal
from .models import (
    IncomeSource, EmergencyFund, IndividualDashboard,
    ExpenseAlert, FinancialGoal
)
from .serializers import (
    IncomeSourceSerializer, EmergencyFundSerializer, IndividualDashboardSerializer,
    ExpenseAlertSerializer, FinancialGoalSerializer, IndividualOverviewSerializer,
    WalletSerializer, TransactionSerializer
)
from student_module.models import Wallet, Transaction


class IncomeSourceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows income sources to be viewed or edited.
    """
    serializer_class = IncomeSourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return IncomeSource.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EmergencyFundViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows emergency funds to be viewed or edited.
    """
    serializer_class = EmergencyFundSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyFund.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IndividualDashboardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows individual dashboards to be viewed or edited.
    """
    serializer_class = IndividualDashboardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return IndividualDashboard.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExpenseAlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows expense alerts to be viewed or edited.
    """
    serializer_class = ExpenseAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExpenseAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        """Mark an alert as read."""
        alert = self.get_object()
        alert.mark_as_read()
        return Response({'status': _('Alert marked as read')})

    @action(detail=False, methods=['patch'])
    def mark_all_read(self, request):
        """Mark all alerts as read."""
        alerts = self.get_queryset().filter(is_read=False)
        alerts.update(is_read=True, read_at=timezone.now())
        return Response({'status': _(f'{alerts.count()} alerts marked as read')})


class FinancialGoalViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows financial goals to be viewed or edited.
    """
    serializer_class = FinancialGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FinancialGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):
        """Update the current amount for a financial goal."""
        goal = self.get_object()
        current_amount = request.data.get('current_amount')

        if current_amount is not None:
            goal.current_amount = current_amount
            goal.save()
            return Response({'status': _('Goal progress updated')})

        return Response({'error': _('current_amount is required')}, status=status.HTTP_400_BAD_REQUEST)


class IndividualOverviewView(APIView):
    """
    API endpoint for individual financial overview.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Get wallet balance
        try:
            wallet = Wallet.objects.get(user=user)
            wallet_balance = wallet.balance
        except Wallet.DoesNotExist:
            wallet_balance = 0.00

        # Calculate monthly income
        current_month = timezone.now().replace(day=1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)

        monthly_income = IncomeSource.objects.filter(
            user=user,
            is_active=True
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        # Calculate monthly expenses
        monthly_expenses = Transaction.objects.filter(
            user=user,
            transaction_date__gte=current_month,
            transaction_date__lt=next_month,
            transaction_type='EXP'
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        # Emergency fund progress
        try:
            emergency_fund = EmergencyFund.objects.get(user=user)
            emergency_fund_progress = emergency_fund.progress_percentage
        except EmergencyFund.DoesNotExist:
            emergency_fund_progress = 0.00

        # Active goals count
        active_goals_count = FinancialGoal.objects.filter(
            user=user,
            status='ACTIVE'
        ).count()

        # Unread alerts count
        unread_alerts_count = ExpenseAlert.objects.filter(
            user=user,
            is_read=False
        ).count()

        # Recent transactions (last 10)
        recent_transactions = Transaction.objects.filter(
            user=user
        ).order_by('-transaction_date')[:10]

        # Create the response data
        response_data = {
            'wallet_balance': wallet_balance,
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'emergency_fund_progress': emergency_fund_progress,
            'active_goals_count': active_goals_count,
            'unread_alerts_count': unread_alerts_count,
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data
        }

        return Response(response_data)


class WalletManagementView(APIView):
    """
    API endpoint for wallet management operations.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Get wallet information."""
        try:
            wallet = Wallet.objects.get(user=request.user)
            serializer = WalletSerializer(wallet)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
            return Response(
                {'error': _('Wallet not found')},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request, *args, **kwargs):
        """Add money to wallet."""
        amount = request.data.get('amount')
        description = request.data.get('description', 'Wallet deposit')

        if not amount or Decimal(amount) <= 0:
            return Response(
                {'error': _('Valid amount is required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={'balance': Decimal('0.00')}
        )

        wallet.balance += Decimal(amount)
        wallet.save()

        # Create transaction record
        Transaction.objects.create(
            user=request.user,
            amount=Decimal(amount),
            transaction_type='INC',
            description=description,
            transaction_date=timezone.now().date()
        )

        return Response({
            'message': _(f'Successfully added {amount} to wallet'),
            'new_balance': wallet.balance
        }, status=status.HTTP_201_CREATED)


class ExpenseTrackingView(APIView):
    """
    API endpoint for expense tracking and budget monitoring.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Get expense summary for current month."""
        user = request.user
        current_month = timezone.now().replace(day=1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)

        # Get monthly expenses by category
        expenses_by_category = Transaction.objects.filter(
            user=user,
            transaction_date__gte=current_month,
            transaction_date__lt=next_month,
            transaction_type='EXP'
        ).values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')

        # Get total monthly expenses
        total_expenses = Transaction.objects.filter(
            user=user,
            transaction_date__gte=current_month,
            transaction_date__lt=next_month,
            transaction_type='EXP'
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        # Get monthly income
        monthly_income = IncomeSource.objects.filter(
            user=user,
            is_active=True
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        # Calculate remaining budget
        remaining_budget = monthly_income - total_expenses

        return Response({
            'current_month': current_month.strftime('%Y-%m'),
            'monthly_income': monthly_income,
            'total_expenses': total_expenses,
            'remaining_budget': remaining_budget,
            'expenses_by_category': list(expenses_by_category)
        })

    def post(self, request, *args, **kwargs):
        """Add a new expense."""
        amount = request.data.get('amount')
        description = request.data.get('description')
        category_id = request.data.get('category')

        if not all([amount, description, category_id]):
            return Response(
                {'error': _('amount, description, and category are required')},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            wallet = Wallet.objects.get(user=request.user)
            if wallet.balance < Decimal(amount):
                return Response(
                    {'error': _('Insufficient wallet balance')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Deduct from wallet
            wallet.balance -= Decimal(amount)
            wallet.save()

            # Create transaction
            Transaction.objects.create(
                user=request.user,
                amount=Decimal(amount),
                transaction_type='EXP',
                description=description,
                category_id=category_id,
                transaction_date=timezone.now().date()
            )

            return Response({
                'message': _(f'Expense of {amount} recorded successfully'),
                'new_balance': wallet.balance
            }, status=status.HTTP_201_CREATED)

        except Wallet.DoesNotExist:
            return Response(
                {'error': _('Wallet not found')},
                status=status.HTTP_404_NOT_FOUND
            )
