from django.core.management.base import BaseCommand

from django_ixctl.models import Routeserver, RouteserverConfig


class Command(BaseCommand):

    """
    Regenerate updates routeserver configs
    """

    def add_arguments(self, parser):
        parser.add_argument("--only-id", help="only process this id", type=int)
        parser.add_argument(
            "--force", action="store_true", help="force regen of configs"
        )

    def handle(self, *args, **kwargs):
        force = kwargs["force"]

        if kwargs["only_id"]:
            pk = kwargs["only_id"]
            qset = Routeserver.objects.filter(id=pk)
            print(f"only running for route server id {pk}")

        else:
            qset = Routeserver.objects.all()

        for rs in qset:
            routeserver_config, created = RouteserverConfig.objects.get_or_create(
                routeserver=rs
            )
            if force or created or rs.routeserver_config.outdated:
                self.stdout.write(f"Regenerating {rs}")
                rs.routeserver_config.generate()
                self.stdout.write("Done")
