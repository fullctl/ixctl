from django.apps import AppConfig

from django_ixctl.auth import Permissions


class DjangoIxctlConfig(AppConfig):
    name = "django_ixctl"
    label = "django_ixctl"

    def ready(self):
        import django_ixctl.signals
