from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from .models import DailySalary, ExpenseTracking, DailySummary
from .serializers import DailySalarySerializer, ExpenseTrackingSerializer, DailySummarySerializer


class DailySalaryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows daily salaries to be viewed or edited.
    """
    serializer_class = DailySalarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DailySalary.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ExpenseTrackingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows expenses to be viewed or edited.
    """
    serializer_class = ExpenseTrackingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ExpenseTracking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DailySummaryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows daily summaries to be viewed or edited.
    """
    serializer_class = DailySummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DailySummary.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate_summary(self, request):
        """Generate or update daily summary for a specific date."""
        user = request.user
        date = request.data.get('date')

        if not date:
            return Response({'error': _('Date is required')}, status=400)

        # Get or create summary
        summary, created = DailySummary.objects.get_or_create(
            user=user,
            date=date,
            defaults={'date': date}
        )

        # Update the summary
        summary.update_summary()

        serializer = self.get_serializer(summary)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard data for the current month."""
        user = request.user
        today = timezone.now().date()

        # Current month data
        current_month = today.replace(day=1)
        next_month = current_month.replace(month=current_month.month + 1) if current_month.month < 12 else current_month.replace(year=current_month.year + 1, month=1)

        # Monthly totals
        monthly_salary = DailySalary.objects.filter(
            user=user,
            date__gte=current_month,
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        monthly_expenses = ExpenseTracking.objects.filter(
            user=user,
            date__gte=current_month,
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Today's data
        today_salary = DailySalary.objects.filter(
            user=user,
            date=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        today_expenses = ExpenseTracking.objects.filter(
            user=user,
            date=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Recent summaries (last 7 days)
        recent_summaries = DailySummary.objects.filter(
            user=user,
            date__gte=today - timezone.timedelta(days=7)
        ).order_by('-date')[:7]

        recent_data = []
        for summary in recent_summaries:
            recent_data.append({
                'date': summary.date,
                'salary': summary.total_salary,
                'expenses': summary.total_expenses,
                'savings': summary.net_savings
            })

        dashboard_data = {
            'monthly_overview': {
                'total_salary': monthly_salary,
                'total_expenses': monthly_expenses,
                'net_savings': monthly_salary - monthly_expenses
            },
            'today_overview': {
                'salary': today_salary,
                'expenses': today_expenses,
                'savings': today_salary - today_expenses
            },
            'recent_summaries': recent_data,
            'expense_categories': self._get_expense_categories(user, current_month, next_month)
        }

        return Response(dashboard_data)

    def _get_expense_categories(self, user, start_date, end_date):
        """Get expense breakdown by category for the period."""
        categories = ExpenseTracking.objects.filter(
            user=user,
            date__gte=start_date,
            date__lt=end_date
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')

        return list(categories)

    @action(detail=False, methods=['get'])
    def reports(self, request):
        """Get detailed financial reports."""
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response({'error': _('start_date and end_date are required')}, status=400)

        # Salary data
        salaries = DailySalary.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).values('date').annotate(
            total_salary=Sum('amount')
        ).order_by('date')

        # Expense data
        expenses = ExpenseTracking.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).values('date').annotate(
            total_expenses=Sum('amount')
        ).order_by('date')

        # Category breakdown
        category_breakdown = ExpenseTracking.objects.filter(
            user=user,
            date__gte=start_date,
            date__lte=end_date
        ).values('category').annotate(
            total=Sum('amount'),
            count=models.Count('id')
        ).order_by('-total')

        report = {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_salary': sum(item['total_salary'] for item in salaries),
                'total_expenses': sum(item['total_expenses'] for item in expenses),
                'net_savings': sum(item['total_salary'] for item in salaries) - sum(item['total_expenses'] for item in expenses)
            },
            'daily_data': {
                'salaries': list(salaries),
                'expenses': list(expenses)
            },
            'category_breakdown': list(category_breakdown)
        }

        return Response(report)
