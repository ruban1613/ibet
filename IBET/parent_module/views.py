from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from core.throttling import OTPGenerationThrottle, WalletAccessThrottle, SensitiveOperationsThrottle
from .models import ParentDashboard, AlertSettings, StudentMonitoring, ParentAlert, ParentOTPRequest
from .serializers import (
    ParentDashboardSerializer, AlertSettingsSerializer, StudentMonitoringSerializer,
    ParentAlertSerializer, StudentWalletAccessSerializer, StudentOverviewSerializer,
    ParentOTPRequestSerializer, GenerateOTPSerializer
)
from student_module.models import ParentStudentLink, Wallet, Transaction
from django.utils import timezone
import random
import string


class ParentDashboardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows parent dashboards to be viewed or edited.
    """
    serializer_class = ParentDashboardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ParentDashboard.objects.filter(parent=self.request.user)

    def perform_create(self, serializer):
        parent_dashboard, created = ParentDashboard.objects.get_or_create(parent=self.request.user)
        serializer.instance = parent_dashboard
        serializer.save()


class AlertSettingsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows alert settings to be viewed or edited.
    """
    serializer_class = AlertSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AlertSettings.objects.filter(parent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)


class StudentMonitoringViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows student monitoring sessions to be viewed or edited.
    """
    serializer_class = StudentMonitoringSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StudentMonitoring.objects.filter(parent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)


class ParentAlertViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows parent alerts to be viewed or edited.
    """
    serializer_class = ParentAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ParentAlert.objects.filter(parent=self.request.user)

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)

    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        """Mark an alert as read."""
        alert = self.get_object()
        alert.status = 'READ'
        alert.read_at = timezone.now()
        alert.save()
        return Response({'status': _('Alert marked as read')})

    @action(detail=True, methods=['patch'])
    def mark_action_taken(self, request, pk=None):
        """Mark an alert as having action taken."""
        alert = self.get_object()
        alert.status = 'ACTION_TAKEN'
        alert.save()
        return Response({'status': _('Action recorded')})


class StudentWalletAccessView(APIView):
    """
    API endpoint for parent to access student's wallet and approve extra funds.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [SensitiveOperationsThrottle, WalletAccessThrottle]

    def post(self, request, *args, **kwargs):
        serializer = StudentWalletAccessSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            student_id = serializer.validated_data['student_id']
            amount_needed = serializer.validated_data['amount_needed']
            reason = serializer.validated_data['reason']

            # Create monitoring record
            StudentMonitoring.objects.create(
                parent=request.user,
                student_id=student_id,
                wallet_accessed=True,
                notes=f"Requested extra funds: {amount_needed} for {reason}"
            )

            # Here you would typically generate and send OTP
            # For now, we'll just return success
            return Response({
                'message': _('Wallet access request processed. OTP sent to student.'),
                'student_id': student_id,
                'amount_requested': amount_needed
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentOverviewView(APIView):
    """
    API endpoint for parent to view student's financial overview.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [WalletAccessThrottle]

    def get(self, request, student_id, *args, **kwargs):
        # Check if parent is linked to this student
        if not ParentStudentLink.objects.filter(parent=request.user, student_id=student_id).exists():
            return Response(
                {'error': _('You are not authorized to view this student\'s data')},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create monitoring record
        StudentMonitoring.objects.create(
            parent=request.user,
            student_id=student_id,
            wallet_accessed=False,
            notes="Viewed student overview"
        )

        serializer = StudentOverviewSerializer({'student_id': student_id})
        return Response(serializer.data)


class LinkedStudentsView(APIView):
    """
    API endpoint to get all students linked to the parent.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        linked_students = ParentStudentLink.objects.filter(parent=request.user).select_related('student')
        students_data = []

        for link in linked_students:
            student = link.student
            try:
                wallet = Wallet.objects.get(user=student)
                wallet_balance = wallet.balance
            except Wallet.DoesNotExist:
                wallet_balance = 0.00

            students_data.append({
                'id': student.id,
                'username': student.username,
                'email': student.email,
                'wallet_balance': wallet_balance,
                'linked_since': link.id  # Using id as proxy for creation date
            })

        return Response({
            'linked_students': students_data,
            'total_students': len(students_data)
        })


class ParentOTPRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows OTP requests to be viewed.
    """
    serializer_class = ParentOTPRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ParentOTPRequest.objects.filter(parent=self.request.user)


class GenerateOTPView(APIView):
    """
    API endpoint for parent to generate OTP for student wallet access.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OTPGenerationThrottle, SensitiveOperationsThrottle]

    def post(self, request, *args, **kwargs):
        serializer = GenerateOTPSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            student_id = serializer.validated_data['student_id']
            amount_requested = serializer.validated_data['amount_requested']
            reason = serializer.validated_data['reason']

            # Generate 6-digit OTP
            otp_code = ''.join(random.choices(string.digits, k=6))

            # Set expiration time (10 minutes from now)
            expires_at = timezone.now() + timezone.timedelta(minutes=10)

            # Create OTP request
            otp_request = ParentOTPRequest.objects.create(
                parent=request.user,
                student_id=student_id,
                otp_code=otp_code,
                amount_requested=amount_requested,
                reason=reason,
                expires_at=expires_at
            )

            # Create monitoring record
            StudentMonitoring.objects.create(
                parent=request.user,
                student_id=student_id,
                otp_generated=True,
                notes=f"Generated OTP {otp_code} for {amount_requested} - {reason}"
            )

            # Here you would send the OTP to the student via SMS/email
            # For now, we'll return the OTP in the response (in production, don't do this!)
            return Response({
                'message': _('OTP generated successfully. Please share this OTP with your student.'),
                'otp_request_id': otp_request.id,
                'otp_code': otp_code,  # Remove this in production!
                'expires_at': otp_request.expires_at,
                'student_id': student_id,
                'amount_requested': amount_requested
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




