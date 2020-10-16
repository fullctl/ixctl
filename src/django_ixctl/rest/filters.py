from django.db.models.functions import Lower
from django.db.models import CharField
from rest_framework.filters import OrderingFilter
from django.core.exceptions import FieldDoesNotExist


class CaseInsensitiveOrderingFilter(OrderingFilter):
    def __init__(self, ordering_fields):
        self.ordering_fields = ordering_fields

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if len(ordering) > 0:
            # Only supports single field ordering
            ordering = ordering[0]

            # Since we got ordering from self.get_ordering() we are
            # assuming the ordering is valid
            field = queryset.model._meta.get_field(ordering.replace("-", ""))

            # For CharacterFields, use case insensitive ordering
            if type(field) == CharField:
                if ordering.startswith("-"):
                    queryset = queryset.order_by(
                        Lower(ordering.replace("-", "")).desc()
                    )
                else:
                    queryset = queryset.order_by(Lower(ordering))
                return queryset

            else:
                return queryset.order_by(ordering)

        return queryset
