from django.conf import settings
from django_ixctl.models import InternetExchange
from django_peeringdb.models.concrete import Network

def account_service(request):

    context = {}

    # TODO abstract so other auth services can be
    # defined
    if settings.MANAGED_BY_OAUTH:
        context.update(
            account_service={
                "urls": {
                    "create_org": f"{settings.OAUTH_TWENTYC_HOST}/account/org/create/",
                    "manage_org": f"{settings.OAUTH_TWENTYC_HOST}/account/?org={request.org.slug}",
                },
            },
            oauth_manages_org=settings.MANAGED_BY_OAUTH,
        )


    return context


def permissions(request):
    context = {}

    instances = [request.org]
    ops = [("c", "create"), ("r", "read"), ("u", "update"), ("d", "delete")]

    is_accessible = request.org in request.org.accessible(request.user)

    for op, name in ops:
        key = f"{name}_instance"
        if name == "read":
            context[key] = is_accessible
        else:
            context[key] = request.perms.check(request.org, op)

    return {"permissions": context}
