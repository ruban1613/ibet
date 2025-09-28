from django.contrib import admin
from .models import DailySalary, ExpenseTracking, DailySummary


@admin.register(DailySalary)
class DailySalaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'amount', 'payment_type', 'created_at')
    list_filter = ('payment_type', 'date', 'created_at')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'date'


@admin.register(ExpenseTracking)
class ExpenseTrackingAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'category', 'amount', 'is_essential', 'created_at')
    list_filter = ('category', 'is_essential', 'date', 'created_at')
    search_fields = ('user__username', 'description')
    date_hierarchy = 'date'


@admin.register(DailySummary)
class DailySummaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'total_salary', 'total_expenses', 'net_savings', 'updated_at')
    list_filter = ('date', 'updated_at')
    search_fields = ('user__username',)
    date_hierarchy = 'date'
    readonly_fields = ('total_salary', 'total_expenses', 'net_savings', 'essential_expenses', 'non_essential_expenses')
