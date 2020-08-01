from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


from django_ixctl.models import (
    Routeserver,
    RouteserverConfig,
)


class Command(BaseCommand):

    """
    Regenerate updates routeserver configs
    """

    # def add_arguments(self, parser):
    #    parser.add_argument("--pdburl", default="https://www.peeringdb.com/api")

    def handle(self, *args, **kwargs):

        qset = Routeserver.objects.all()

        for rs in qset:
            rsconf = RouteserverConfig.objects.get(rs=rs)
            if rs.rsconf.outdated:
                self.stdout.write("Regenerating {rs}")
                rs.rsconf.generate()
                self.stdout.write("Done")
