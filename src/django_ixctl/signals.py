from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in

from django_ixctl.util import (
    create_networks_from_verified_asns,
)

@receiver(user_logged_in)
def handle_login(sender, **kwargs):
    user = kwargs.get("user")
    create_networks_from_verified_asns(user)
