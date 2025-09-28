from django.apps import AppConfig


class RetireeModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'retiree_module'

    def ready(self):
        import retiree_module.translation  # noqa
