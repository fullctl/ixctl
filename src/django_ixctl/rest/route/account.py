from rest_framework import routers


router = routers.DefaultRouter()


def route(viewset):
    if hasattr(viewset, "ref_tag"):
        ref_tag = viewset.ref_tag
    else:
        ref_tag = viewset.serializer_class.ref_tag

    router.register(ref_tag, viewset, basename=ref_tag)
