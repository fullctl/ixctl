from fullctl.django.models import Task
from fullctl.django.tasks import register

import django_ixctl.models.ixctl as models


@register
class RsConfGenerate(Task):

    """
    Regenerate RS config


    arguments to pass to `create_task`:

        - config_routeserver_id (id of config_routeserver instance)
    """

    class TaskMeta:
        # limit of 1, but this will be per rs
        # see generate_limit_id below
        limit = 1

    class Meta:
        proxy = True

    class HandleRef:
        tag = "task_config_routeserver_gen"

    @property
    def generate_limit_id(self):
        """
        We want the task limit to be per config_routeserver so we
        include the config_routeserver id in the limit_id for the task
        """
        return self.param["args"][0]

    def run(self, config_routeserver_id, *args, **kwargs):
        """
        Regenerate the config_routeserverig
        """
        config_routeserver = models.RouteserverConfig.objects.get(
            id=config_routeserver_id
        )
        config_routeserver.generate()
