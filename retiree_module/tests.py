from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils.translation import activate
from .models import IncomeSource, ExpenseCategory, Forecast, RetireeProfile
from decimal import Decimal

User = get_user_model()


class IncomeSourceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser_model', password='testpass')

    def test_income_source_creation(self):
        income = IncomeSource.objects.create(
            user=self.user,
            source_type='Pension',
            amount=2000.00,
            frequency='MONTHLY'
        )
        self.assertEqual(income.source_type, 'Pension')
        self.assertEqual(income.amount, 2000.00)


class ExpenseCategoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser_expense_model', password='testpass')

    def test_expense_category_creation(self):
        expense = ExpenseCategory.objects.create(
            user=self.user,
            category_name='Health',
            budgeted_amount=Decimal('500.00')
        )
        self.assertEqual(expense.category_name, 'Health')
        self.assertEqual(expense.get_variance(), Decimal('500.00'))


class ForecastModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser_forecast_model', password='testpass')

    def test_forecast_creation(self):
        forecast = Forecast.objects.create(
            user=self.user,
            forecast_type='BUDGET',
            period='MONTHLY',
            predicted_amount=3000.00,
            confidence_level=85
        )
        self.assertEqual(forecast.forecast_type, 'BUDGET')
        self.assertEqual(forecast.predicted_amount, 3000.00)


class IncomeSourceAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='retiree', password='testpass', persona='RETIREE')
        self.client.force_authenticate(user=self.user)
        activate('en')
        self.url = reverse('retiree:income-source-list')

    def test_create_income_source(self):
        data = {
            # 'user' should not be in the payload; it's set from the request user.
            'source_type': 'Pension',
            'amount': '5000.00',
            'frequency': 'MONTHLY',
            'description': 'Monthly pension'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(IncomeSource.objects.count(), 1)
        income_source = IncomeSource.objects.get()
        self.assertEqual(income_source.source_type, 'Pension')
        self.assertEqual(income_source.user, self.user)

    def test_list_income_sources(self):
        IncomeSource.objects.create(
            user=self.user, source_type='Pension', amount='5000.00', frequency='MONTHLY'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class ExpenseCategoryAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='retiree_expense_user', password='testpass', persona='RETIREE')
        self.client.force_authenticate(user=self.user)
        activate('en')
        self.url = reverse('retiree:expense-category-list')

    def test_create_expense_category(self):
        data = {
            'category_name': 'Healthcare',
            'budgeted_amount': '400.00',
            'description': 'Monthly medical checkups'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExpenseCategory.objects.count(), 1)
        expense = ExpenseCategory.objects.get()
        self.assertEqual(expense.category_name, 'Healthcare')
        self.assertEqual(expense.user, self.user)


class RetireeProfileAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='retiree_profile_user', password='testpass', persona='RETIREE')
        self.client.force_authenticate(user=self.user)
        activate('en')
        self.url = reverse('retiree:retiree-profile-list')

    def test_create_retiree_profile(self):
        """
        Ensure we can create a new retiree profile.
        """
        data = {
            'pension_amount': '2500.00',
            'savings': '150000.00',
            'alert_threshold': '800.00'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RetireeProfile.objects.count(), 1)
        profile = RetireeProfile.objects.get()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.pension_amount, Decimal('2500.00'))


class ForecastViewSetAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='forecast_user', password='testpass', persona='RETIREE')
        self.client.force_authenticate(user=self.user)
        activate('en')

        # Create some income and expenses for the user to forecast
        IncomeSource.objects.create(user=self.user, source_type='Pension', amount='3000.00')
        IncomeSource.objects.create(user=self.user, source_type='Investments', amount='500.00')
        ExpenseCategory.objects.create(user=self.user, category_name='Rent', budgeted_amount='1200.00')
        ExpenseCategory.objects.create(user=self.user, category_name='Groceries', budgeted_amount='400.00')

    def test_generate_forecast_action(self):
        """
        Ensure the generate_forecast custom action creates a forecast correctly.
        """
        url = reverse('retiree:forecast-generate-forecast')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Forecast.objects.count(), 1)

        forecast = Forecast.objects.get()
        self.assertEqual(forecast.user, self.user)
        # Expected: (3000 + 500) - (1200 + 400) = 3500 - 1600 = 1900
        self.assertEqual(forecast.predicted_amount, Decimal('1900.00'))

    def test_reports_action(self):
        """
        Ensure the reports custom action returns correct aggregated data.
        """
        # Also create a forecast to test the count
        Forecast.objects.create(user=self.user, forecast_type='BUDGET', period='MONTHLY', predicted_amount='1900.00')

        url = reverse('retiree:forecast-reports')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_income'], Decimal('3500.00'))
        self.assertEqual(response.data['total_budgeted_expenses'], Decimal('1600.00'))
        self.assertEqual(response.data['budget_variance'], Decimal('1600.00')) # budgeted - actual (0)
        self.assertEqual(response.data['forecasts_count'], 1)


class RetireeTransactionAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='retiree_trans_user', password='testpass', persona='RETIREE')
        self.client.force_authenticate(user=self.user)
        activate('en')
        self.url = reverse('retiree:retiree-transaction-list')

    def test_create_retiree_transaction(self):
        """
        Ensure we can create a new retiree transaction.
        """
        data = {
            'amount': '150.50',
            'transaction_type': 'EXP',
            'description': 'Groceries'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], '150.50')
        self.assertEqual(response.data['transaction_type'], 'EXP')

    def test_list_retiree_transactions(self):
        """
        Ensure we can list retiree transactions.
        """
        from .models import RetireeTransaction
        RetireeTransaction.objects.create(user=self.user, amount='100.00', transaction_type='EXP')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class AlertViewSetAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='retiree_alert_user', password='testpass', persona='RETIREE')
        self.client.force_authenticate(user=self.user)
        activate('en')
        self.list_url = reverse('retiree:alert-list')

    def test_create_alert(self):
        """
        Ensure we can create a new alert.
        """
        data = {
            'alert_type': 'BUDGET',
            'message': 'Nearing budget limit for healthcare.',
            'threshold': '500.00',
            'is_active': True
        }
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        from .models import Alert
        self.assertEqual(Alert.objects.count(), 1)
        self.assertEqual(Alert.objects.get().alert_type, 'BUDGET')

    def test_list_alerts(self):
        """
        Ensure we can list alerts for the authenticated user.
        """
        from .models import Alert
        Alert.objects.create(user=self.user, alert_type='EXPENSE', message='High spending this week')
        # Create an alert for another user to ensure it's not listed
        other_user = User.objects.create_user(username='other_user', password='testpass')
        Alert.objects.create(user=other_user, alert_type='BUDGET', message='Other user alert')

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['message'], 'High spending this week')

    def test_delete_alert(self):
        from .models import Alert
        alert = Alert.objects.create(user=self.user, alert_type='EXPENSE', message='To be deleted')
        detail_url = reverse('retiree:alert-detail', kwargs={'pk': alert.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Alert.objects.count(), 0)