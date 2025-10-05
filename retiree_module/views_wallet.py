"""
Secure wallet views for Retiree Module.
Provides secure wallet operations with OTP protection and monitoring.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from django.db import models
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService, SecurityUtils
from core.security_monitoring_fixed import SecurityEventManager, AuditService
from core.permissions import OTPGenerationPermission, OTPVerificationPermission
from .models_wallet import RetireeWallet, RetireeWalletTransaction, RetireeWalletOTPRequest
from .serializers_wallet import RetireeWalletSerializer, RetireeWalletTransactionSerializer
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal


class RetireeWalletViewSet(viewsets.ModelViewSet):
    """
    Secure API endpoint for retiree wallet management.
    """
    serializer_class = RetireeWalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        return RetireeWallet.objects.filter(user=self.request.user)

    def get_object(self):
        try:
            return RetireeWallet.objects.get(user=self.request.user)
        except RetireeWallet.DoesNotExist:
            raise RetireeWallet.DoesNotExist("Retiree wallet not found")

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get wallet balance securely"""
        try:
            wallet = self.get_object()
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['WALLET_ACCESS'],
                request.user.id,
                {'action': 'balance_check'}
            )

            return Response({
                'balance': wallet.balance,
                'pension_balance': wallet.pension_balance,
                'emergency_fund': wallet.emergency_fund,
                'available_balance': wallet.available_balance,
                'monthly_expense_limit': wallet.monthly_expense_limit,
                'is_locked': wallet.is_locked,
                'last_transaction_at': wallet.last_transaction_at
            })
        except RetireeWallet.DoesNotExist:
            return Response({'error': _('Wallet not found')}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Secure deposit to wallet"""
        try:
            try:
                wallet = self.get_object()
            except RetireeWallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = RetireeWallet.objects.create(
                    user=request.user,
                    balance=Decimal('0.00'),
                    pension_balance=Decimal('0.00'),
                    emergency_fund=Decimal('0.00'),
                    monthly_expense_limit=Decimal('5000.00')
                )

            amount = Decimal(request.data.get('amount', 0))
            description = request.data.get('description', 'Deposit')

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'wallet_deposit', threshold=5, time_window_minutes=30
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            new_balance = wallet.deposit_pension(amount, description)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'deposit',
                amount,
                {'description': description}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'transfer_type': 'credit'}
            )

            return Response({
                'message': _('Deposit successful'),
                'new_balance': new_balance
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def deposit_pension(self, request):
        """Secure pension deposit to wallet"""
        try:
            try:
                wallet = self.get_object()
            except RetireeWallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = RetireeWallet.objects.create(
                    user=request.user,
                    balance=Decimal('0.00'),
                    pension_balance=Decimal('0.00'),
                    emergency_fund=Decimal('0.00'),
                    monthly_expense_limit=Decimal('5000.00')
                )

            amount = Decimal(request.data.get('amount', 0))
            description = request.data.get('description', 'Pension Deposit')

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'pension_deposit', threshold=3, time_window_minutes=60
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            new_balance = wallet.deposit_pension(amount, description)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'pension_deposit',
                amount,
                {'description': description}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'type': 'pension_deposit'}
            )

            return Response({
                'message': _('Pension deposit successful'),
                'new_balance': new_balance,
                'pension_balance': wallet.pension_balance
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def deposit_emergency(self, request):
        """Secure emergency fund deposit to wallet"""
        try:
            try:
                wallet = self.get_object()
            except RetireeWallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = RetireeWallet.objects.create(
                    user=request.user,
                    balance=Decimal('0.00'),
                    pension_balance=Decimal('0.00'),
                    emergency_fund=Decimal('0.00'),
                    monthly_expense_limit=Decimal('5000.00')
                )

            amount = Decimal(request.data.get('amount', 0))
            description = request.data.get('description', 'Emergency Fund Deposit')

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            new_balance = wallet.deposit_emergency(amount, description)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'emergency_deposit',
                amount,
                {'description': description}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'type': 'emergency_deposit'}
            )

            return Response({
                'message': _('Emergency fund deposit successful'),
                'new_balance': new_balance,
                'emergency_fund': wallet.emergency_fund
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Secure withdrawal from wallet"""
        try:
            try:
                wallet = self.get_object()
            except RetireeWallet.DoesNotExist:
                return Response({'error': _('Wallet not found')}, status=status.HTTP_404_NOT_FOUND)

            amount = Decimal(request.data.get('amount', 0))
            description = request.data.get('description', 'Withdrawal')
            use_pension_fund = request.data.get('use_pension_fund', False)

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'wallet_withdrawal', threshold=3, time_window_minutes=15
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            new_balance = wallet.withdraw(amount, description, use_pension_fund)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'withdrawal',
                amount,
                {'description': description, 'use_pension_fund': use_pension_fund}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'type': 'withdrawal', 'use_pension_fund': use_pension_fund}
            )

            return Response({
                'message': _('Withdrawal successful'),
                'new_balance': new_balance
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def monthly_expenses(self, request):
        """Get monthly expense summary"""
        try:
            wallet = self.get_object()
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            expenses = RetireeWalletTransaction.objects.filter(
                wallet=wallet,
                transaction_type='WITHDRAWAL',
                created_at__gte=current_month
            ).aggregate(
                total=Sum('amount'),
                count=models.Count('id')
            )

            return Response({
                'total_expenses': expenses['total'] or Decimal('0.00'),
                'expense_count': expenses['count'] or 0,
                'monthly_limit': wallet.monthly_expense_limit,
                'remaining_limit': wallet.monthly_expense_limit - (expenses['total'] or Decimal('0.00'))
            })

        except RetireeWallet.DoesNotExist:
            return Response({'error': _('Wallet not found')}, status=status.HTTP_404_NOT_FOUND)


class RetireeWalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View transaction history for retiree wallets.
    """
    serializer_class = RetireeWalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        return RetireeWalletTransaction.objects.filter(wallet__user=self.request.user)


class GenerateRetireeWalletOTPView(APIView):
    """
    Secure API endpoint for generating OTP for retiree wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPGenerationPermission]
    throttle_classes = [OTPGenerationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        operation_type = request.data.get('operation_type')
        amount = request.data.get('amount')
        description = request.data.get('description', '')

        if not operation_type:
            return Response({'error': _('Operation type is required')}, status=status.HTTP_400_BAD_REQUEST)

        # Generate secure OTP
        otp_request_data = OTPSecurityService.create_otp_request(
            request.user.id,
            'retiree_wallet_operation'
        )

        # Set expiration time (10 minutes from now)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)

        # Create OTP request
        otp_request = RetireeWalletOTPRequest.objects.create(
            user=request.user,
            operation_type=operation_type,
            amount=amount,
            description=description,
            otp_code='',  # Don't store the actual OTP
            expires_at=expires_at,
            cache_key=otp_request_data['cache_key']
        )

        # Audit the OTP generation
        AuditService.audit_otp_operation(
            request.user.id,
            'generate',
            True,
            {
                'operation_type': operation_type,
                'amount': amount,
                'description': description
            }
        )

        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['OTP_GENERATED'],
            request.user.id,
            {
                'operation_type': operation_type,
                'amount': amount,
                'expires_at': expires_at.isoformat()
            }
        )

        return Response({
            'message': _('OTP generated successfully for wallet operation'),
            'otp_request_id': otp_request.id,
            'operation_type': operation_type,
            'expires_at': expires_at,
            'note': _('The OTP has been securely generated and must be shared with the user directly.')
        }, status=status.HTTP_201_CREATED)


class VerifyRetireeWalletOTPView(APIView):
    """
    Secure API endpoint for verifying OTP for retiree wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPVerificationPermission]
    throttle_classes = [OTPVerificationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        otp_code = request.data.get('otp_code')
        otp_request_id = request.data.get('otp_request_id')

        if not otp_code or not otp_request_id:
            return Response({'error': _('OTP code and request ID are required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_request = RetireeWalletOTPRequest.objects.get(
                id=otp_request_id,
                user=request.user,
                is_used=False
            )

            if otp_request.is_expired():
                otp_request.delete()
                SecurityEventManager.log_event(
                    SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                    request.user.id,
                    {'reason': 'OTP expired'}
                )
                return Response({'error': _('OTP has expired')}, status=status.HTTP_400_BAD_REQUEST)

            # Validate OTP using security service
            cache_key = f"otp_request_{otp_request.id}"
            is_valid, error_message = OTPSecurityService.validate_otp(
                request.user.id,
                otp_code,
                cache_key,
                'retiree_wallet_operation'
            )

            if not is_valid:
                SecurityEventManager.log_event(
                    SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                    request.user.id,
                    {'reason': error_message}
                )
                return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)

            # Mark OTP as used
            otp_request.mark_as_used()

            # Audit successful verification
            AuditService.audit_otp_operation(
                request.user.id,
                'verify',
                True,
                {
                    'operation_type': otp_request.operation_type,
                    'amount': otp_request.amount
                }
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_VERIFIED'],
                request.user.id,
                {
                    'operation_type': otp_request.operation_type,
                    'amount': otp_request.amount,
                    'success': True
                }
            )

            return Response({
                'message': _('OTP verified successfully'),
                'operation_type': otp_request.operation_type,
                'amount': otp_request.amount,
                'description': otp_request.description
            })

        except RetireeWalletOTPRequest.DoesNotExist:
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                request.user.id,
                {'reason': 'Invalid OTP request'}
            )
            return Response({'error': _('Invalid OTP request')}, status=status.HTTP_400_BAD_REQUEST)
