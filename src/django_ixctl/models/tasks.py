from fullctl.django.models import Task
from fullctl.django.tasks import register

import django_ixctl.models.ixctl as models


@register
class RsConfGenerate(Task):

    """
    Regenerate RS config


    arguments to pass to `create_task`:

        - routeserver_config_id (id of routeserver_config instance)
    """

    class TaskMeta:
        # limit of 1, but this will be per rs
        # see generate_limit_id below
        limit = 1

    class Meta:
        proxy = True

    class HandleRef:
        tag = "task_routeserver_config_gen"

    @property
    def generate_limit_id(self):
        """
        We want the task limit to be per routeserver_config so we
        include the routeserver_config id in the limit_id for the task
        """
        return self.param["args"][0]

    def run(self, routeserver_config_id, *args, **kwargs):
        """
        Regenerate the routeserver_config
        """
        routeserver_config = models.RouteserverConfig.objects.get(
            id=routeserver_config_id
        )
        routeserver_config.generate()
