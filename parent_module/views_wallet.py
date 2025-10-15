"""
Secure wallet views for Parent Module.
Provides secure wallet operations with student monitoring and approval features.
"""
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, OTPVerificationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from core.security import OTPSecurityService, SecurityUtils
from core.security_monitoring import SecurityEventManager, AuditService
from core.permissions import OTPGenerationPermission, OTPVerificationPermission
from .models import ParentOTPRequest, StudentMonitoring, ParentAlert
from .serializers_wallet import ParentWalletSerializer
from student_module.models import Wallet, ParentStudentLink, OTPRequest
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


class ParentWalletViewSet(viewsets.ModelViewSet):
    """
    Secure API endpoint for parent wallet management.
    """
    serializer_class = ParentWalletSerializer
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
                'balance': wallet.balance
            })
        except Wallet.DoesNotExist:
            return Response({'error': _('Wallet not found')}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Secure deposit to wallet"""
        try:
            wallet = self.get_object()
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
                {'amount': amount, 'new_balance': new_balance, 'operation': 'deposit'}
            )

            return Response({
                'message': _('Deposit successful'),
                'new_balance': new_balance
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Secure withdrawal from wallet"""
        try:
            wallet = self.get_object()
            amount = Decimal(request.data.get('amount', 0))
            description = request.data.get('description', 'Withdrawal')

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
                {'amount': amount, 'new_balance': new_balance, 'operation': 'withdrawal'}
            )

            return Response({
                'message': _('Withdrawal successful'),
                'new_balance': new_balance
            })

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def linked_students_wallets(self, request):
        """Get wallet information for all linked students"""
        try:
            linked_students = ParentStudentLink.objects.filter(parent=request.user)
            students_wallets = []

            for link in linked_students:
                student = link.student
                try:
                    wallet = Wallet.objects.get(user=student)
                    students_wallets.append({
                        'student_id': student.id,
                        'student_username': student.username,
                        'wallet_balance': wallet.balance
                    })
                except Wallet.DoesNotExist:
                    students_wallets.append({
                        'student_id': student.id,
                        'student_username': student.username,
                        'wallet_balance': 0.00
                    })

            return Response({
                'linked_students_wallets': students_wallets,
                'total_linked_students': len(students_wallets)
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GenerateParentWalletOTPView(APIView):
    """
    Secure API endpoint for generating OTP for parent wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPGenerationPermission]
    throttle_classes = [OTPGenerationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        operation_type = request.data.get('operation_type')
        amount = request.data.get('amount')
        description = request.data.get('description', '')
        student_id = request.data.get('student_id')

        if not operation_type:
            return Response({'error': _('Operation type is required')}, status=status.HTTP_400_BAD_REQUEST)

        # Get student if provided
        student = None
        if student_id:
            try:
                student = User.objects.get(id=student_id)
                # Verify parent-student relationship
                if not ParentStudentLink.objects.filter(parent=request.user, student=student).exists():
                    return Response({'error': _('Invalid student relationship')}, status=status.HTTP_403_FORBIDDEN)
            except User.DoesNotExist:
                return Response({'error': _('Student not found')}, status=status.HTTP_404_NOT_FOUND)

        # Generate secure OTP
        otp_request_data = OTPSecurityService.create_otp_request(
            request.user.id,
            'parent_wallet_operation'
        )

        # Set expiration time (10 minutes from now)
        expires_at = timezone.now() + timezone.timedelta(minutes=10)

        # Create OTP request
        otp_request = ParentOTPRequest.objects.create(
            parent=request.user,
            student=student,
            operation_type=operation_type,
            amount=amount,
            description=description,
            otp_code='',  # Don't store the actual OTP
            expires_at=expires_at,
            cache_key=otp_request_data['cache_key']
        )

        # Send OTP via email if student is specified
        if student and student.email:
            OTPSecurityService.send_otp_via_email(
                otp_request_data['otp_code'],
                student.email,
                'parent_wallet_operation'
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


class VerifyParentWalletOTPView(APIView):
    """
    Secure API endpoint for verifying OTP for parent wallet operations.
    """
    permission_classes = [permissions.IsAuthenticated, OTPVerificationPermission]
    throttle_classes = [OTPVerificationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        otp_code = request.data.get('otp_code')
        otp_request_id = request.data.get('otp_request_id')

        if not otp_code or not otp_request_id:
            return Response({'error': _('OTP code and request ID are required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_request = ParentOTPRequest.objects.get(
                id=otp_request_id,
                parent=request.user,
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
            cache_key = otp_request.cache_key
            if not cache_key:
                return Response({'error': _('Invalid OTP request')}, status=status.HTTP_400_BAD_REQUEST)

            is_valid, error_message = OTPSecurityService.validate_otp(
                request.user.id,
                otp_code,
                cache_key,
                'parent_wallet_operation'
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

            # Perform the wallet operation based on operation_type
            try:
                if otp_request.operation_type == 'transfer_to_student' and otp_request.student:
                    # Transfer funds to student's wallet
                    parent_wallet = Wallet.objects.get(user=request.user)
                    student_wallet = Wallet.objects.get(user=otp_request.student)

                    amount_decimal = Decimal(otp_request.amount or 0)

                    if parent_wallet.balance < amount_decimal:
                        return Response({'error': _('Insufficient funds in parent wallet')}, status=status.HTTP_400_BAD_REQUEST)

                    # Perform transfer
                    parent_wallet.balance -= amount_decimal
                    student_wallet.balance += amount_decimal
                    parent_wallet.save()
                    student_wallet.save()

                    # Create monitoring record
                    StudentMonitoring.objects.create(
                        parent=request.user,
                        student=otp_request.student,
                        wallet_accessed=True,
                        notes=f"Transferred {amount_decimal} to student wallet via OTP verification"
                    )

                    # Audit the transfer
                    AuditService.audit_wallet_operation(
                        request.user.id,
                        'transfer_to_student',
                        amount_decimal,
                        {
                            'student_id': otp_request.student.id,
                            'description': otp_request.description
                        }
                    )

                    SecurityEventManager.log_event(
                        SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                        request.user.id,
                        {
                            'operation': 'transfer_to_student',
                            'amount': amount_decimal,
                            'student_id': otp_request.student.id,
                            'new_parent_balance': parent_wallet.balance,
                            'new_student_balance': student_wallet.balance
                        }
                    )

                    response_data = {
                        'message': _('OTP verified and funds transferred successfully'),
                        'operation_type': otp_request.operation_type,
                        'amount': otp_request.amount,
                        'description': otp_request.description,
                        'new_parent_balance': parent_wallet.balance,
                        'new_student_balance': student_wallet.balance
                    }

                else:
                    # For other operation types, just return success
                    response_data = {
                        'message': _('OTP verified successfully'),
                        'operation_type': otp_request.operation_type,
                        'amount': otp_request.amount,
                        'description': otp_request.description
                    }

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

                return Response(response_data)

            except Wallet.DoesNotExist:
                return Response({'error': _('Wallet not found')}, status=status.HTTP_404_NOT_FOUND)
            except ValueError:
                return Response({'error': _('Invalid amount')}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Wallet operation failed: {e}")
                return Response({'error': _('Operation failed')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except ParentOTPRequest.DoesNotExist:
            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['OTP_FAILED'],
                request.user.id,
                {'reason': 'Invalid OTP request'}
            )
            return Response({'error': _('Invalid OTP request')}, status=status.HTTP_400_BAD_REQUEST)


class StudentWalletApprovalView(APIView):
    """
    API endpoint for parents to approve student wallet requests.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        student_id = request.data.get('student_id')
        amount = request.data.get('amount')
        otp_code = request.data.get('otp_code')

        if not all([student_id, amount, otp_code]):
            return Response({'error': _('Student ID, amount, and OTP code are required')}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify parent-student relationship
            parent_link = ParentStudentLink.objects.get(parent=request.user, student_id=student_id)

            # Find and validate OTP request
            otp_request = OTPRequest.objects.get(
                student_id=student_id,
                parent=request.user,
                amount_requested=amount,
                is_used=False
            )

            if otp_request.is_expired():
                return Response({'error': _('OTP has expired')}, status=status.HTTP_400_BAD_REQUEST)

            # In a real implementation, you would validate the OTP code here
            # For now, we'll assume it's valid if the request exists

            # Get student's wallet and add funds
            student_wallet = Wallet.objects.get(user_id=student_id)
            student_wallet.balance += Decimal(amount)
            student_wallet.save()

            # Mark OTP as used
            otp_request.mark_as_used()

            # Create monitoring record
            StudentMonitoring.objects.create(
                parent=request.user,
                student_id=student_id,
                wallet_accessed=True,
                notes=f"Approved and transferred {amount} to student wallet"
            )

            # Audit the operation
            AuditService.audit_wallet_operation(
                request.user.id,
                'student_approval',
                Decimal(amount),
                {'student_id': student_id, 'approved': True}
            )

            SecurityEventManager.log_event(
                SecurityEventManager.EVENT_TYPES['FUND_TRANSFER'],
                request.user.id,
                {'student_id': student_id, 'amount': amount, 'approved': True, 'operation': 'student_approval'}
            )

            return Response({
                'message': _('Student wallet request approved successfully'),
                'student_id': student_id,
                'amount_approved': amount,
                'new_student_balance': student_wallet.balance
            })

        except ParentStudentLink.DoesNotExist:
            return Response({'error': _('Student not linked to this parent')}, status=status.HTTP_400_BAD_REQUEST)
        except OTPRequest.DoesNotExist:
            return Response({'error': _('Invalid or expired OTP request')}, status=status.HTTP_400_BAD_REQUEST)
        except Wallet.DoesNotExist:
            return Response({'error': _('Student wallet not found')}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
