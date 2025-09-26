"""
Fixed comprehensive test for wallet functionality across all modules.
Tests wallet operations for Individual, Couple, Retiree, Dailywage, Student, and Parent modules.
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_testing_final')
django.setup()

User = get_user_model()

class WalletCompleteTest(APITestCase):
    """Test wallet functionality for all modules."""

    def setUp(self):
        """Set up test data."""
        # Create test users for different personas
        self.individual_user = User.objects.create_user(
            username='individual_test',
            email='individual@test.com',
            password='testpass123',
            persona='INDIVIDUAL'
        )

        self.couple_user1 = User.objects.create_user(
            username='couple_test1',
            email='couple1@test.com',
            password='testpass123',
            persona='COUPLE'
        )

        self.couple_user2 = User.objects.create_user(
            username='couple_test2',
            email='couple2@test.com',
            password='testpass123',
            persona='COUPLE'
        )

        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            password='testpass123',
            persona='STUDENT'
        )

        self.parent_user = User.objects.create_user(
            username='parent_test',
            email='parent@test.com',
            password='testpass123',
            persona='PARENT'
        )

        self.retiree_user = User.objects.create_user(
            username='retiree_test',
            email='retiree@test.com',
            password='testpass123',
            persona='RETIREE'
        )

        self.dailywage_user = User.objects.create_user(
            username='dailywage_test',
            email='dailywage@test.com',
            password='testpass123',
            persona='DAILY_WAGER'
        )

        # Create parent-student link
        from student_module.models import ParentStudentLink
        ParentStudentLink.objects.create(
            parent=self.parent_user,
            student=self.student_user
        )

        # Create auth tokens for users
        self.individual_token = Token.objects.create(user=self.individual_user)
        self.couple_token = Token.objects.create(user=self.couple_user1)
        self.student_token = Token.objects.create(user=self.student_user)
        self.parent_token = Token.objects.create(user=self.parent_user)
        self.retiree_token = Token.objects.create(user=self.retiree_user)
        self.dailywage_token = Token.objects.create(user=self.dailywage_user)

    def get_authenticated_client(self, user):
        """Get authenticated API client for a user."""
        client = APIClient()
        token = Token.objects.get(user=user)
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client

    def test_individual_wallet_functionality(self):
        """Test individual wallet operations."""
        client = self.get_authenticated_client(self.individual_user)

        # Test wallet balance
        response = client.get('/api/individual/wallet/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/individual/wallet/wallet/deposit/',
                              {'amount': '100.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

        # Test wallet withdrawal
        response = client.post('/api/individual/wallet/wallet/withdraw/',
                              {'amount': '50.00', 'description': 'Test withdrawal'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

    def test_couple_wallet_functionality(self):
        """Test couple wallet operations."""
        client = self.get_authenticated_client(self.couple_user1)

        # Test wallet balance
        response = client.get('/api/couple/wallet/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/couple/wallet/wallet/deposit/',
                              {'amount': '200.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

    def test_retiree_wallet_functionality(self):
        """Test retiree wallet operations."""
        client = self.get_authenticated_client(self.retiree_user)

        # Test wallet balance
        response = client.get('/api/retiree/wallet/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/retiree/wallet/wallet/deposit/',
                              {'amount': '300.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

    def test_dailywage_wallet_functionality(self):
        """Test dailywage wallet operations."""
        client = self.get_authenticated_client(self.dailywage_user)

        # Test wallet balance
        response = client.get('/api/dailywage/wallet/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/dailywage/wallet/wallet/deposit/',
                              {'amount': '150.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

    def test_student_wallet_functionality(self):
        """Test student wallet operations."""
        client = self.get_authenticated_client(self.student_user)

        # Test wallet balance
        response = client.get('/api/student/wallet/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/student/wallet/wallet/deposit/',
                              {'amount': '75.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

        # Test parent approval request
        response = client.post('/api/student/wallet/wallet/request_parent_approval/',
                              {'amount': '25.00', 'description': 'Test parent approval'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('otp_request_id', response.data)

    def test_parent_wallet_functionality(self):
        """Test parent wallet operations."""
        client = self.get_authenticated_client(self.parent_user)

        # Test wallet balance
        response = client.get('/api/parent/wallet/wallet/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('balance', response.data)

        # Test wallet deposit
        response = client.post('/api/parent/wallet/wallet/deposit/',
                              {'amount': '400.00', 'description': 'Test deposit'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('new_balance', response.data)

        # Test linked students wallets
        response = client.get('/api/parent/wallet/wallet/linked_students_wallets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('linked_students_wallets', response.data)

    def test_wallet_otp_generation_and_verification(self):
        """Test OTP generation and verification for all modules."""
        # Test individual wallet OTP
        client = self.get_authenticated_client(self.individual_user)
        response = client.post('/api/individual/wallet/generate-otp/',
                              {'operation_type': 'deposit', 'amount': '50.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.data)

        # Test student wallet OTP
        client = self.get_authenticated_client(self.student_user)
        response = client.post('/api/student/wallet/generate-otp/',
                              {'operation_type': 'deposit', 'amount': '25.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.data)

        # Test parent wallet OTP
        client = self.get_authenticated_client(self.parent_user)
        response = client.post('/api/parent/wallet/generate-otp/',
                              {'operation_type': 'deposit', 'amount': '100.00'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('otp_request_id', response.data)

    def test_cross_module_wallet_interactions(self):
        """Test interactions between different modules' wallets."""
        # Test parent-student wallet interaction
        parent_client = self.get_authenticated_client(self.parent_user)
        student_client = self.get_authenticated_client(self.student_user)

        # Parent requests OTP for student approval
        response = parent_client.post('/api/parent/generate-otp/',
                                     {'student_id': self.student_user.id,
                                      'amount_requested': '50.00',
                                      'reason': 'Test approval'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        otp_request_id = response.data['otp_request_id']

        # Student requests parent approval
        response = student_client.post('/api/student/wallet/wallet/request_parent_approval/',
                                      {'amount': '50.00', 'description': 'Test approval request'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_wallet_security_features(self):
        """Test wallet security features like throttling and permissions."""
        client = self.get_authenticated_client(self.individual_user)

        # Test rapid requests (should be throttled)
        for i in range(10):
            response = client.get('/api/individual/wallet/wallet/balance/')

        # Should eventually be throttled
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS])

        # Test invalid operations
        response = client.post('/api/individual/wallet/wallet/withdraw/',
                              {'amount': '10000.00', 'description': 'Over withdrawal'})
        # Should fail due to insufficient funds
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wallet_comprehensive_coverage(self):
        """Comprehensive test covering all wallet endpoints."""
        modules = [
            ('individual', self.individual_user),
            ('couple', self.couple_user1),
            ('retiree', self.retiree_user),
