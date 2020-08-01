from django_grainy.util import Permissions as GrainyPermissions


class Permissions(GrainyPermissions):
    def check(self, *args, **kwargs):
        return True

    def get(self, *args, as_string=False, **kwargs):
        if as_string:
            return "crud"
        return 15
