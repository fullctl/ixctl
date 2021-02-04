from django.core.management.base import BaseCommand

from django_ixctl.models import Routeserver, RouteserverConfig


class Command(BaseCommand):

    """
    Regenerate updates routeserver configs
    """

    # def add_arguments(self, parser):
    #    parser.add_argument("--pdburl", default="https://www.peeringdb.com/api")

    def handle(self, *args, **kwargs):

        qset = Routeserver.objects.all()

        for rs in qset:
            rsconf, created = RouteserverConfig.objects.get_or_create(rs=rs)
            if created or rs.rsconf.outdated:
                self.stdout.write(f"Regenerating {rs}")
                rs.rsconf.generate()
                self.stdout.write("Done")
