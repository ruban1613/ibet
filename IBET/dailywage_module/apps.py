from django.apps import AppConfig


class DailywageModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dailywage_module'

    def ready(self):
        import dailywage_module.translation  # noqa
