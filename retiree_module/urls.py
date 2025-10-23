from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncomeSourceViewSet, ExpenseCategoryViewSet, RetireeProfileViewSet, ForecastViewSet, RetireeTransactionViewSet, AlertViewSet, RetireeAlertViewSet

app_name = "retiree"

router = DefaultRouter(trailing_slash=False)
router.register(r"income-sources", IncomeSourceViewSet, basename="income-source")
router.register(r"expense-categories", ExpenseCategoryViewSet, basename="expense-category")
router.register(r"retiree-profiles", RetireeProfileViewSet, basename="retiree-profile")
router.register(r"forecasts", ForecastViewSet, basename="forecast")
router.register(r"retiree-transactions", RetireeTransactionViewSet, basename="retiree-transaction")
router.register(r"alerts", AlertViewSet, basename="alert")
router.register(r"retiree-alerts", RetireeAlertViewSet, basename="retiree-alert")

urlpatterns = router.urls

# Include wallet-specific URLs
urlpatterns += [
    path('', include('retiree_module.urls_wallet', namespace='retiree_wallet')),
]
