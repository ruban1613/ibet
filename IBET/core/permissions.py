"""
Custom permission classes for enhanced security in the IBET application.
Provides wallet access controls, parent-student relationship validation, and security-based access controls.
"""
from rest_framework import permissions
from django.utils.translation import gettext_lazy as _
from core.security import SecurityUtils


class IsParentOfStudent(permissions.BasePermission):
    """
    Custom permission to check if the requesting user is a parent of the specified student.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if user has parent persona
        if not hasattr(request.user, 'persona') or request.user.persona != 'PARENT':
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # For object-level permissions, check if parent is linked to the specific student
        if hasattr(obj, 'student'):
            return SecurityUtils.validate_user_access(request.user, obj.student)
        return True


class WalletAccessPermission(permissions.BasePermission):
    """
    Permission class for wallet access operations.
    Ensures only authorized users can access wallet functionality.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if user has appropriate persona for wallet access
        allowed_personas = ['STUDENT', 'PARENT', 'INDIVIDUAL', 'COUPLE', 'RETIREE', 'DAILY_WAGER']
        if not hasattr(request.user, 'persona') or request.user.persona not in allowed_personas:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # For wallet-specific operations, ensure ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return True


class SensitiveOperationPermission(permissions.BasePermission):
    """
    Permission class for sensitive operations like fund transfers.
    Provides additional security checks for high-risk operations.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Check if user has verified their identity recently
        # This could be extended to check for recent OTP verification, etc.
        return True


class ParentStudentRelationshipPermission(permissions.BasePermission):
    """
    Permission class specifically for parent-student relationship operations.
    Ensures secure linking and access between parents and students.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Only parents can perform parent-student relationship operations
        if not hasattr(request.user, 'persona') or request.user.persona != 'PARENT':
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # For parent-student link objects, ensure the parent owns the relationship
        if hasattr(obj, 'parent'):
            return obj.parent == request.user
        return True


class OTPGenerationPermission(permissions.BasePermission):
    """
    Permission class for OTP generation operations.
    Ensures only authorized users can generate OTPs.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Only parents can generate OTPs for students
        if not hasattr(request.user, 'persona') or request.user.persona != 'PARENT':
            return False

        return True


class OTPVerificationPermission(permissions.BasePermission):
    """
    Permission class for OTP verification operations.
    Ensures only authorized users can verify OTPs.
    """

    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return False

        # Only students can verify OTPs
        if not hasattr(request.user, 'persona') or request.user.persona != 'STUDENT':
            return False

        return True


class SecurityEventPermission(permissions.BasePermission):
    """
    Permission class for security monitoring and audit operations.
    Restricts access to security-related functionality.
    """

    def has_permission(self, request, view):
        # Only superusers or staff can access security monitoring
        return request.user and (request.user.is_superuser or request.user.is_staff)
