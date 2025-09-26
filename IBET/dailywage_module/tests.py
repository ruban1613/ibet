from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from .models import DailySalary, ExpenseTracking, DailySummary


class DailyWageModuleModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_daily_salary_creation(self):
        salary = DailySalary.objects.create(
            user=self.user,
            date=date.today(),
            amount=Decimal('500.00'),
            payment_type='CASH',
            description='Daily wage'
        )
        self.assertEqual(salary.user, self.user)
        self.assertEqual(salary.amount, Decimal('500.00'))
        self.assertEqual(str(salary), f"{self.user.username}'s salary on {date.today()}: 500.00")

    def test_expense_tracking_creation(self):
        expense = ExpenseTracking.objects.create(
            user=self.user,
            date=date.today(),
            category='FOOD',
            amount=Decimal('50.00'),
            description='Lunch'
        )
        self.assertEqual(expense.user, self.user)
        self.assertEqual(expense.category, 'FOOD')
        self.assertEqual(expense.amount, Decimal('50.00'))

    def test_daily_summary_update(self):
        # Create salary and expense
        salary = DailySalary.objects.create(
            user=self.user,
            date=date.today(),
            amount=Decimal('500.00')
        )
        expense = ExpenseTracking.objects.create(
            user=self.user,
            date=date.today(),
            category='FOOD',
            amount=Decimal('50.00')
        )

        # Create and update summary
        summary = DailySummary.objects.create(user=self.user, date=date.today())
        summary.update_summary()

        self.assertEqual(summary.total_salary, Decimal('500.00'))
        self.assertEqual(summary.total_expenses, Decimal('50.00'))
        self.assertEqual(summary.net_savings, Decimal('450.00'))


class DailyWageModuleAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_daily_salary_list_create(self):
        # Test list (should be empty)
        url = reverse('daily-salary-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Test create
        data = {
            'date': date.today().isoformat(),
            'amount': '500.00',
            'payment_type': 'CASH',
            'description': 'Daily wage'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DailySalary.objects.count(), 1)
        self.assertEqual(DailySalary.objects.get().amount, Decimal('500.00'))

    def test_expense_tracking_list_create(self):
        # Test list (should be empty)
        url = reverse('expense-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Test create
        data = {
            'date': date.today().isoformat(),
            'category': 'FOOD',
            'amount': '50.00',
            'description': 'Lunch'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExpenseTracking.objects.count(), 1)
        self.assertEqual(ExpenseTracking.objects.get().category, 'FOOD')

    def test_daily_summary_generate(self):
        # Create salary and expense first
        DailySalary.objects.create(
            user=self.user,
            date=date.today(),
            amount=Decimal('500.00')
        )
        ExpenseTracking.objects.create(
            user=self.user,
            date=date.today(),
            category='FOOD',
            amount=Decimal('50.00')
        )

        # Test generate summary
        url = reverse('summary-generate-summary')
        data = {'date': date.today().isoformat()}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DailySummary.objects.count(), 1)

        summary = DailySummary.objects.get()
        self.assertEqual(summary.total_salary, Decimal('500.00'))
        self.assertEqual(summary.total_expenses, Decimal('50.00'))
        self.assertEqual(summary.net_savings, Decimal('450.00'))

    def test_dashboard_endpoint(self):
        # Create some test data
        today = date.today()
        DailySalary.objects.create(user=self.user, date=today, amount=Decimal('500.00'))
        ExpenseTracking.objects.create(user=self.user, date=today, category='FOOD', amount=Decimal('50.00'))

        url = reverse('summary-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('monthly_overview', data)
        self.assertIn('today_overview', data)
        self.assertIn('recent_summaries', data)
        self.assertIn('expense_categories', data)

    def test_reports_endpoint(self):
        # Create test data
        today = date.today()
        yesterday = today - timedelta(days=1)

        from decimal import Decimal
        DailySalary.objects.create(user=self.user, date=today, amount=Decimal('500.00'))
        DailySalary.objects.create(user=self.user, date=yesterday, amount=Decimal('450.00'))

        ExpenseTracking.objects.create(user=self.user, date=today, category='FOOD', amount=Decimal('50.00'))
        ExpenseTracking.objects.create(user=self.user, date=yesterday, category='TRANSPORT', amount=Decimal('30.00'))

        url = reverse('summary-reports')
        params = {
            'start_date': yesterday.isoformat(),
            'end_date': today.isoformat()
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn('summary', data)
        self.assertIn('daily_data', data)
        self.assertIn('category_breakdown', data)

        # Check totals
        from decimal import Decimal
        self.assertEqual(Decimal(data['summary']['total_salary']), Decimal('950.00'))
        self.assertEqual(Decimal(data['summary']['total_expenses']), Decimal('80.00'))
        self.assertEqual(Decimal(data['summary']['net_savings']), Decimal('870.00'))

    def test_unauthenticated_access(self):
        # Remove authentication
        self.client.force_authenticate(user=None)

        url = reverse('daily-salary-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_daily_salary_update_delete(self):
        # Create a salary entry
        salary = DailySalary.objects.create(
            user=self.user,
            date=date.today(),
            amount=Decimal('500.00'),
            payment_type='CASH',
            description='Daily wage'
        )

        # Test update
        update_url = reverse('daily-salary-detail', kwargs={'pk': salary.pk})
        update_data = {
            'date': date.today().isoformat(),
            'amount': '600.00',
            'payment_type': 'BANK_TRANSFER',
            'description': 'Updated wage'
        }
        response = self.client.put(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        salary.refresh_from_db()
        self.assertEqual(salary.amount, Decimal('600.00'))
        self.assertEqual(salary.payment_type, 'BANK_TRANSFER')

        # Test delete
        response = self.client.delete(update_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DailySalary.objects.count(), 0)

    def test_expense_tracking_update_delete(self):
        # Create an expense entry
        expense = ExpenseTracking.objects.create(
            user=self.user,
            date=date.today(),
            category='FOOD',
            amount=Decimal('50.00'),
            description='Lunch'
        )

        # Test update
        update_url = reverse('expense-detail', kwargs={'pk': expense.pk})
        update_data = {
            'date': date.today().isoformat(),
            'category': 'TRANSPORT',
            'amount': '30.00',
            'description': 'Bus fare',
            'is_essential': True
        }
        response = self.client.put(update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expense.refresh_from_db()
        self.assertEqual(expense.category, 'TRANSPORT')
        self.assertEqual(expense.amount, Decimal('30.00'))
        self.assertTrue(expense.is_essential)

        # Test delete
        response = self.client.delete(update_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ExpenseTracking.objects.count(), 0)

    def test_daily_summary_list_retrieve(self):
        # Create a summary
        summary = DailySummary.objects.create(user=self.user, date=date.today())
        summary.update_summary()

        # Test list
        list_url = reverse('summary-list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # Test retrieve
        detail_url = reverse('summary-detail', kwargs={'pk': summary.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['date'], date.today().isoformat())

    def test_generate_summary_without_date(self):
        """Test generate_summary action without providing date."""
        url = reverse('summary-generate-summary')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_reports_endpoint_missing_params(self):
        """Test reports endpoint with missing parameters."""
        url = reverse('summary-reports')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_expense_categories_calculation(self):
        """Test that expense categories are correctly calculated in dashboard."""
        # Create expenses in different categories
        today = date.today()
        ExpenseTracking.objects.create(user=self.user, date=today, category='FOOD', amount=Decimal('50.00'))
        ExpenseTracking.objects.create(user=self.user, date=today, category='FOOD', amount=Decimal('30.00'))
        ExpenseTracking.objects.create(user=self.user, date=today, category='TRANSPORT', amount=Decimal('20.00'))

        url = reverse('summary-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        categories = response.data['expense_categories']
        # Should have 2 categories: FOOD and TRANSPORT
        self.assertEqual(len(categories), 2)

        # Find FOOD category
        food_category = next(cat for cat in categories if cat['category'] == 'FOOD')
        self.assertEqual(Decimal(food_category['total']), Decimal('80.00'))

        # Find TRANSPORT category
        transport_category = next(cat for cat in categories if cat['category'] == 'TRANSPORT')
        self.assertEqual(Decimal(transport_category['total']), Decimal('20.00'))

    def test_user_isolation(self):
        """Test that users can only access their own data."""
        # Create another user
        other_user = get_user_model().objects.create_user(
            username='other_user',
            email='other@example.com',
            password='testpass123'
        )

        # Create data for other user
        DailySalary.objects.create(
            user=other_user,
            date=date.today(),
            amount=Decimal('1000.00')
        )

        # Test that current user cannot see other user's data
        url = reverse('daily-salary-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Should be empty for current user

    def test_model_str_methods(self):
        """Test string representations of models."""
        salary = DailySalary.objects.create(
            user=self.user,
            date=date.today(),
            amount=Decimal('500.00')
        )
        expected_str = f"{self.user.username}'s salary on {date.today()}: 500.00"
        self.assertEqual(str(salary), expected_str)

        expense = ExpenseTracking.objects.create(
            user=self.user,
            date=date.today(),
            category='FOOD',
            amount=Decimal('50.00')
        )
        expected_str = f"{self.user.username}'s FOOD expense on {date.today()}: 50.00"
        self.assertEqual(str(expense), expected_str)

        summary = DailySummary.objects.create(user=self.user, date=date.today())
        expected_str = f"{self.user.username}'s summary for {date.today()}"
        self.assertEqual(str(summary), expected_str)

    def test_unique_constraints(self):
        """Test unique constraints on models."""
        # Test DailySalary unique constraint (user, date)
        DailySalary.objects.create(
            user=self.user,
            date=date.today(),
            amount=Decimal('500.00')
        )

        # Try to create another salary for same user and date
        with self.assertRaises(Exception):  # Should raise IntegrityError
            DailySalary.objects.create(
                user=self.user,
                date=date.today(),
                amount=Decimal('300.00')
            )

    def test_decimal_field_precision(self):
        """Test that decimal fields maintain precision."""
        salary = DailySalary.objects.create(
            user=self.user,
            date=date.today(),
            amount=Decimal('123.456789')
        )
        salary.refresh_from_db()
        self.assertEqual(salary.amount, Decimal('123.46'))  # Model field has decimal_places=2

        expense = ExpenseTracking.objects.create(
            user=self.user,
            date=date.today(),
            category='FOOD',
            amount=Decimal('45.678901')
        )
        expense.refresh_from_db()
        self.assertEqual(expense.amount, Decimal('45.68'))  # Model field has decimal_places=2
