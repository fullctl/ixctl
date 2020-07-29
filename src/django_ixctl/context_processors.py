from django.conf import settings
def account_service(request):

    context = {}


    # TODO abstract so other auth services can be
    # defined
    if settings.ORGANIZATION_PROVIDED_BY_OAUTH:
        context.update(account_service={
            "urls": {
                "create_org" : f"{settings.TWENTYC_ENDPOINT}/account/org/create/",
                "manage_org" : f"{settings.TWENTYC_ENDPOINT}/account/?org={request.org.slug}",
            },
        }, oauth_manages_org=settings.ORGANIZATION_PROVIDED_BY_OAUTH)

    return context




def permissions(request):
    context = {}

    instances = [request.org]
    ops = [("c", "create"), ("r", "read"), ("u", "update"), ("d", "delete")]

    if hasattr(request, "app_id"):
        for op, name in ops:
            key = f"{name}_instance"
            context[key] = request.perms.check([request.org, request.app_id], op)

    for instance in instances:
        if not instance:
            continue
        for namespace in instance.permission_namespaces:
            for op, name in ops:
                key = "{}_{}_{}".format(
                    name, instance.HandleRef.tag, namespace.replace(".", "__")
                )
                context[key] = request.perms.check([instance, namespace], op)

    print(context)
    return {"permissions": context}
