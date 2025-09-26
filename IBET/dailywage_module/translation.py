from modeltranslation.translator import translator, TranslationOptions
from .models import DailySalary, ExpenseTracking

# Translation options for model fields
class DailySalaryTranslationOptions(TranslationOptions):
    fields = ('description',)

class ExpenseTrackingTranslationOptions(TranslationOptions):
    fields = ('description',)

# Register translation options
translator.register(DailySalary, DailySalaryTranslationOptions)
translator.register(ExpenseTracking, ExpenseTrackingTranslationOptions)
