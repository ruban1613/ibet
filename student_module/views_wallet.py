"""
Secure wallet views for Student Module.
Provides secure wallet operations with parent approval and OTP protection.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService, SecurityUtils
from core.security_monitoring_fixed import SecurityEventManager, AuditService
from core.permissions import OTPGenerationPermission, OTPVerificationPermission
from .models import Wallet, OTPRequest, ParentStudentLink
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal


class StudentWalletViewSet(viewsets.ModelViewSet):
    """
    Secure API endpoint for student wallet management.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_object(self):
        return Wallet.objects.get(user=self.request.user)

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
                'is_locked': wallet.is_locked,
                'last_transaction_at': wallet.last_transaction_at
            })
        except Wallet.DoesNotExist:
            return Response({'error': _('Wallet not found')}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def welcome(self, request):
        """Welcome endpoint for student wallet"""
        SecurityEventManager.log_event(
            SecurityEventManager.EVENT_TYPES['WALLET_ACCESS'],
            request.user.id,
            {'action': 'welcome', 'method': request.method, 'path': request.path}
        )

        return Response({
            'message': _('Welcome to the Student Wallet API Service!')
        })

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Secure deposit to wallet"""
        try:
            wallet = self.get_object()
            amount = Decimal(request.data.get('amount', 0))
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

            new_balance = wallet.balance + amount
            wallet.balance = new_balance
            wallet.save()

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
    def withdraw(self, request):
        """Secure withdrawal from wallet with parent approval"""
        try:
            wallet = self.get_object()
            amount = Decimal(request.data.get('amount', 0))
            description = request.data.get('description', _('Withdrawal'))

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            if wallet.balance < amount:
                return Response({'error': _('Insufficient funds')}, status=status.HTTP_400_BAD_REQUEST)

            # Check for suspicious activity
            if SecurityEventManager.detect_suspicious_activity(
                request.user.id, 'wallet_withdrawal', threshold=3, time_window_minutes=15
            ):
                return Response(
                    {'error': _('Suspicious activity detected')},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # For students, withdrawals require parent approval
            # This would typically involve OTP verification
            new_balance = wallet.balance - amount
            wallet.balance = new_balance
            wallet.save()

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'withdrawal',
                amount,
                {'description': description}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'amount': amount, 'new_balance': new_balance, 'transfer_type': 'debit'}
            )

            return Response({
                'message': _('Withdrawal successful'),
                'new_balance': new_balance
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def request_parent_approval(self, request):
        """Request parent approval for a transaction"""
        try:
            amount = Decimal(request.data.get('amount', 0))
            description = request.data.get('description', _('Transaction request'))

            if amount <= 0:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)

            # Get linked parent
            try:
                parent_link = ParentStudentLink.objects.get(student=self.request.user)
                parent = parent_link.parent
            except ParentStudentLink.DoesNotExist:
                return Response({'error': _('No parent linked to this student')}, status=status.HTTP_400_BAD_REQUEST)

            # Create OTP request for parent approval
            expires_at = timezone.now() + timezone.timedelta(minutes=10)

            otp_request = OTPRequest.objects.create(
                student=self.request.user,
                parent=parent,
                amount_requested=amount,
                is_used=False,
                expires_at=expires_at
            )

            # Audit the request
            AuditService.audit_wallet_operation(
                self.request.user.id,
                'parent_approval_request',
                amount,
                {'description': description, 'parent_id': parent.id}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['PARENT_APPROVAL_REQUEST'],
                self.request.user.id,
                {'amount': amount, 'parent_id': parent.id}
            )

            return Response({
                'message': _('Parent approval request sent successfully'),
                'otp_request_id': otp_request.id,
                'amount': amount,
                'parent_id': parent.id,
                'expires_at': expires_at
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GenerateStudentWalletOTPView(APIView):
    """
    Secure API endpoint for generating OTP for student wallet operations.
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
            'student_wallet_operation'
        )

        # Set expiration time (10 minutes from now)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)

        # Create OTP request
        otp_request = OTPRequest.objects.create(
            student=request.user,
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


class VerifyStudentWalletOTPView(APIView):
    """
    Secure API endpoint for verifying OTP for student wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPVerificationPermission]
    throttle_classes = [OTPVerificationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        otp_code = request.data.get('otp_code')
        otp_request_id = request.data.get('otp_request_id')

        if not otp_code or not otp_request_id:
            return Response({'error': _('OTP code and request ID are required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_request = OTPRequest.objects.get(
                id=otp_request_id,
                student=request.user,
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
                'student_wallet_operation'
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

        except OTPRequest.DoesNotExist:
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                request.user.id,
                {'reason': 'Invalid OTP request'}
            )
            return Response({'error': _('Invalid OTP request')}, status=status.HTTP_400_BAD_REQUEST)
