from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    BudgetViewSet, CategoryViewSet, TransactionViewSet, SelectPersonaView,
    ReminderViewSet, ChatMessageViewSet, DailyLimitViewSet, VerifyOTPView, OTPRequestViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'reminders', ReminderViewSet, basename='reminder')
router.register(r'chat-messages', ChatMessageViewSet, basename='chat-message')
router.register(r'daily-limits', DailyLimitViewSet, basename='daily-limit')
router.register(r'otp-requests', OTPRequestViewSet, basename='otp-request')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('users/select-persona/', SelectPersonaView.as_view(), name='select-persona'),
    # Add the token authentication endpoint here, it will be available at /api/token-auth/
    path('token-auth/', obtain_auth_token, name='api_token_auth'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    # Include wallet URLs
    path('wallet/', include('student_module.urls_wallet')),
]
