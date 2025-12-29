from django.apps import AppConfig


class EmployersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'org.employers'

    def ready(self):
        import org.employers.signals  # noqa
