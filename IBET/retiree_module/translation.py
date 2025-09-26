from modeltranslation.translator import translator, TranslationOptions
from .models import IncomeSource, ExpenseCategory, Forecast, Alert

# Translation options for model fields
class IncomeSourceTranslationOptions(TranslationOptions):
    fields = ('source_type', 'description')

class ExpenseCategoryTranslationOptions(TranslationOptions):
    fields = ('category_name', 'description')

class ForecastTranslationOptions(TranslationOptions):
    fields = ('notes',)

class AlertTranslationOptions(TranslationOptions):
    fields = ('message',)

# Register translation options
translator.register(IncomeSource, IncomeSourceTranslationOptions)
translator.register(ExpenseCategory, ExpenseCategoryTranslationOptions)
translator.register(Forecast, ForecastTranslationOptions)
translator.register(Alert, AlertTranslationOptions)
