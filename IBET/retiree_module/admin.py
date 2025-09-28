from django.contrib import admin
from .models import IncomeSource, ExpenseCategory, Forecast, Alert, RetireeProfile, RetireeTransaction, RetireeAlert


@admin.register(IncomeSource)
class IncomeSourceAdmin(admin.ModelAdmin):
    list_display = ('user', 'source_type', 'amount', 'frequency', 'created_at')
    list_filter = ('frequency', 'created_at')
    search_fields = ('user__username', 'source_type')


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'category_name', 'budgeted_amount', 'actual_spent', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'category_name')


@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ('user', 'forecast_type', 'period', 'predicted_amount', 'confidence_level', 'created_at')
    list_filter = ('forecast_type', 'period', 'created_at')
    search_fields = ('user__username', 'forecast_type')


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'alert_type', 'message', 'threshold', 'is_active', 'created_at')
    list_filter = ('alert_type', 'is_active', 'created_at')
    search_fields = ('user__username', 'alert_type', 'message')


@admin.register(RetireeProfile)
class RetireeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'pension_amount', 'savings', 'alert_threshold')
    search_fields = ('user__username',)


@admin.register(RetireeTransaction)
class RetireeTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'transaction_date', 'description')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('user__username', 'description')


@admin.register(RetireeAlert)
class RetireeAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'triggered_on', 'message')
    list_filter = ('triggered_on',)
    search_fields = ('user__username', 'message')
