from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DailySalaryViewSet, ExpenseTrackingViewSet, DailySummaryViewSet

router = DefaultRouter()
router.register(r'daily-salaries', DailySalaryViewSet, basename='daily-salary')
router.register(r'expenses', ExpenseTrackingViewSet, basename='expense')
router.register(r'summaries', DailySummaryViewSet, basename='summary')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]

# Include wallet-specific URLs
urlpatterns += [
    path('wallet/', include('dailywage_module.urls_wallet')),
]
