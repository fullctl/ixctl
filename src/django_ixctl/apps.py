from django.apps import AppConfig


class DjangoIxctlConfig(AppConfig):
    name = "django_ixctl"
    label = "django_ixctl"

    def ready(self):
        import django_ixctl.signals
