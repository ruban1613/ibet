"""
Secure wallet views for Daily Wage Module.
Provides secure wallet operations with OTP protection and monitoring.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService, SecurityUtils
from core.security_monitoring_fixed import SecurityEventManager, AuditService
from core.permissions import OTPGenerationPermission, OTPVerificationPermission, IsDailyWageUser
from .models_wallet import DailyWageWallet, DailyWageWalletTransaction, DailyWageWalletOTPRequest
from .serializers_wallet import DailyWageWalletSerializer, DailyWageWalletTransactionSerializer
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal


class DailyWageWalletViewSet(viewsets.ModelViewSet):
    """
    Secure API endpoint for daily wage wallet management.
    """
    serializer_class = DailyWageWalletSerializer
    permission_classes = [permissions.IsAuthenticated, IsDailyWageUser]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        return DailyWageWallet.objects.filter(user=self.request.user)

    def get_object(self):
        try:
            return DailyWageWallet.objects.get(user=self.request.user)
        except DailyWageWallet.DoesNotExist:
            raise DailyWageWallet.DoesNotExist("Daily wage wallet not found")

    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get wallet balance securely"""
        try:
            wallet = self.get_object()
        except DailyWageWallet.DoesNotExist:
            # Create wallet if it doesn't exist
            wallet = DailyWageWallet.objects.create(
                user=request.user,
                balance=Decimal('0.00'),
                daily_earnings=Decimal('0.00'),
                emergency_reserve=Decimal('0.00'),
                weekly_target=Decimal('0.00'),
                monthly_goal=Decimal('0.00')
            )

        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['WALLET_ACCESS'],
            request.user.id,
            {'action': 'balance_check'}
        )

        return Response({
            'balance': wallet.balance,
            'daily_earnings': wallet.daily_earnings,
            'emergency_reserve': wallet.emergency_reserve,
            'available_balance': wallet.available_balance,
            'weekly_target': wallet.weekly_target,
            'monthly_goal': wallet.monthly_goal,
            'weekly_progress': wallet.weekly_progress,
            'is_locked': wallet.is_locked,
            'last_transaction_at': wallet.last_transaction_at
        })

    @action(detail=False, methods=['get'])
    def welcome(self, request):
        """Welcome endpoint for daily wage wallet"""
        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['WALLET_ACCESS'],
            request.user.id,
            {'action': 'welcome', 'method': request.method, 'path': request.path}
        )

        return Response({
            'message': _('Welcome to the Daily Wage Wallet API Service!')
        })

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Secure deposit to wallet"""
        try:
            try:
                wallet = self.get_object()
            except DailyWageWallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = DailyWageWallet.objects.create(
                    user=request.user,
                    balance=Decimal('0.00'),
                    daily_earnings=Decimal('0.00'),
                    emergency_reserve=Decimal('0.00'),
                    weekly_target=Decimal('0.00'),
                    monthly_goal=Decimal('0.00')
                )

            amount_raw = request.data.get('amount', 0)
            try:
                amount = Decimal(amount_raw)
            except Exception:
                return Response({'error': _('Invalid amount format')}, status=status.HTTP_400_BAD_REQUEST)

            description = request.data.get('description', _('Deposit'))

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

            new_balance = wallet.add_daily_earnings(amount, description)

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
    def add_earnings(self, request):
        """Securely add daily earnings to wallet"""
        try:
            try:
                wallet = self.get_object()
            except DailyWageWallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = DailyWageWallet.objects.create(
                    user=request.user,
                    balance=Decimal('0.00'),
                    daily_earnings=Decimal('0.00'),
                    emergency_reserve=Decimal('0.00'),
                    weekly_target=Decimal('0.00'),
                    monthly_goal=Decimal('0.00')
                )

            amount_raw = request.data.get('amount', 0)
            try:
                amount = Decimal(amount_raw)
            except Exception:
                return Response({'error': _('Invalid amount format')}, status=status.HTTP_400_BAD_REQUEST)

            description = request.data.get('description', _('Daily Earnings'))

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'daily_earnings', threshold=5, time_window_minutes=30
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            new_balance = wallet.add_daily_earnings(amount, description)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'daily_earnings',
                amount,
                {'description': description}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'type': 'daily_earnings', 'transfer_type': 'credit'}
            )

            return Response({
                'message': _('Daily earnings added successfully'),
                'new_balance': new_balance,
                'daily_earnings': wallet.daily_earnings,
                'weekly_progress': wallet.weekly_progress
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Secure withdrawal from wallet"""
        try:
            try:
                wallet = self.get_object()
            except DailyWageWallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = DailyWageWallet.objects.create(
                    user=request.user,
                    balance=Decimal('0.00'),
                    daily_earnings=Decimal('0.00'),
                    emergency_reserve=Decimal('0.00'),
                    weekly_target=Decimal('0.00'),
                    monthly_goal=Decimal('0.00')
                )

            amount_raw = request.data.get('amount', 0)
            try:
                amount = Decimal(amount_raw)
            except Exception:
                return Response({'error': _('Invalid amount format')}, status=status.HTTP_400_BAD_REQUEST)

            description = request.data.get('description', _('Withdrawal'))
            is_essential = request.data.get('is_essential', False)

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

            new_balance = wallet.withdraw(amount, description, is_essential)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'withdrawal',
                amount,
                {'description': description, 'is_essential': is_essential}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'is_essential': is_essential, 'transfer_type': 'debit'}
            )

            return Response({
                'message': _('Withdrawal successful'),
                'new_balance': new_balance
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def transfer_to_emergency(self, request):
        """Transfer money to emergency reserve"""
        try:
            try:
                wallet = self.get_object()
            except DailyWageWallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = DailyWageWallet.objects.create(
                    user=request.user,
                    balance=Decimal('0.00'),
                    daily_earnings=Decimal('0.00'),
                    emergency_reserve=Decimal('0.00'),
                    weekly_target=Decimal('0.00'),
                    monthly_goal=Decimal('0.00')
                )

            amount_raw = request.data.get('amount', 0)
            try:
                amount = Decimal(amount_raw)
            except Exception:
                return Response({'error': _('Invalid amount format')}, status=status.HTTP_400_BAD_REQUEST)

            description = request.data.get('description', _('Emergency Reserve Transfer'))

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            new_balance = wallet.transfer_to_emergency(amount, description)

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'emergency_transfer',
                amount,
                {'description': description}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'type': 'emergency_reserve', 'transfer_type': 'transfer'}
            )

            return Response({
                'message': _('Transfer to emergency reserve successful'),
                'new_balance': new_balance,
                'emergency_reserve': wallet.emergency_reserve
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def weekly_summary(self, request):
        """Get weekly earnings and expense summary"""
        try:
            try:
                wallet = self.get_object()
            except DailyWageWallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = DailyWageWallet.objects.create(
                    user=request.user,
                    balance=Decimal('0.00'),
                    daily_earnings=Decimal('0.00'),
                    emergency_reserve=Decimal('0.00'),
                    weekly_target=Decimal('0.00'),
                    monthly_goal=Decimal('0.00')
                )

            current_week_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(days=timezone.now().weekday())

            # Get weekly earnings
            earnings = DailyWageWalletTransaction.objects.filter(
                wallet=wallet,
                transaction_type='DAILY_EARNINGS',
                created_at__gte=current_week_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            # Get weekly expenses
            expenses = DailyWageWalletTransaction.objects.filter(
                wallet=wallet,
                transaction_type='WITHDRAWAL',
                created_at__gte=current_week_start
            ).aggregate(
                total=Sum('amount'),
                essential=Sum('amount', filter=models.Q(is_essential_expense=True)),
                non_essential=Sum('amount', filter=models.Q(is_essential_expense=False))
            )

            return Response({
                'weekly_earnings': earnings,
                'weekly_expenses': expenses['total'] or Decimal('0.00'),
                'essential_expenses': expenses['essential'] or Decimal('0.00'),
                'non_essential_expenses': expenses['non_essential'] or Decimal('0.00'),
                'weekly_target': wallet.weekly_target,
                'progress_percentage': wallet.weekly_progress,
                'remaining_target': wallet.weekly_target - earnings,
                'alert_triggered': wallet.balance < wallet.alert_threshold
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly earnings and expense summary"""
        try:
            try:
                wallet = self.get_object()
            except DailyWageWallet.DoesNotExist:
                # Create wallet if it doesn't exist
                wallet = DailyWageWallet.objects.create(
                    user=request.user,
                    balance=Decimal('0.00'),
                    daily_earnings=Decimal('0.00'),
                    emergency_reserve=Decimal('0.00'),
                    weekly_target=Decimal('0.00'),
                    monthly_goal=Decimal('0.00')
                )

            current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Get monthly earnings
            earnings = DailyWageWalletTransaction.objects.filter(
                wallet=wallet,
                transaction_type='DAILY_EARNINGS',
                created_at__gte=current_month_start
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

            # Get monthly expenses
            expenses = DailyWageWalletTransaction.objects.filter(
                wallet=wallet,
                transaction_type='WITHDRAWAL',
                created_at__gte=current_month_start
            ).aggregate(
                total=Sum('amount'),
                essential=Sum('amount', filter=models.Q(is_essential_expense=True)),
                non_essential=Sum('amount', filter=models.Q(is_essential_expense=False))
            )

            # Calculate monthly progress percentage
            progress_percentage = 0
            if wallet.monthly_goal > 0:
                progress_percentage = min((earnings / wallet.monthly_goal) * 100, 100)

            return Response({
                'monthly_earnings': earnings,
                'monthly_expenses': expenses['total'] or Decimal('0.00'),
                'essential_expenses': expenses['essential'] or Decimal('0.00'),
                'non_essential_expenses': expenses['non_essential'] or Decimal('0.00'),
                'monthly_goal': wallet.monthly_goal,
                'progress_percentage': progress_percentage,
                'remaining_goal': wallet.monthly_goal - earnings,
                'alert_triggered': wallet.balance < wallet.alert_threshold
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DailyWageWalletTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View transaction history for daily wage wallets.
    """
    serializer_class = DailyWageWalletTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        return DailyWageWalletTransaction.objects.filter(wallet__user=self.request.user)


class GenerateDailyWageWalletOTPView(APIView):
    """
    Secure API endpoint for generating OTP for daily wage wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPGenerationPermission]
    throttle_classes = [OTPGenerationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        operation_type = request.data.get('operation_type')
        amount = request.data.get('amount')
        description = request.data.get('description', '')

        if not operation_type:
            return Response({'error': _('Operation type is required')}, status=status.HTTP_400_BAD_REQUEST)

        # Implement rate limiting check here (additional to throttle_classes)
        user = request.user
        from django.core.cache import cache
        cache_key = f"otp_gen_limit_{user.id}"
        count = cache.get(cache_key, 0)
        if count >= 5:
            return Response({'error': _('OTP generation rate limit exceeded')}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        cache.set(cache_key, count + 1, timeout=3600)  # 1 hour window

        # Generate secure OTP
        otp_request_data = OTPSecurityService.create_otp_request(
            request.user.id,
            'dailywage_wallet_operation'
        )

        # Set expiration time (10 minutes from now)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)

        # Create OTP request
        otp_request = DailyWageWalletOTPRequest.objects.create(
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


class VerifyDailyWageWalletOTPView(APIView):
    """
    Secure API endpoint for verifying OTP for daily wage wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPVerificationPermission]
    throttle_classes = [OTPVerificationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        otp_code = request.data.get('otp_code')
        otp_request_id = request.data.get('otp_request_id')

        if not otp_code or not otp_request_id:
            return Response({'error': _('OTP code and request ID are required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_request = DailyWageWalletOTPRequest.objects.get(
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
                'dailywage_wallet_operation'
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

        except DailyWageWalletOTPRequest.DoesNotExist:
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                request.user.id,
                {'reason': 'Invalid OTP request'}
            )
            return Response({'error': _('Invalid OTP request')}, status=status.HTTP_400_BAD_REQUEST)
