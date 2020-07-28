from common.inet.exceptions import PdbNotFoundError


def pdb_lookup(cls, **filters):
    try:
        return cls.objects.get(**filters)
    except cls.DoesNotExist:
        raise PdbNotFoundError(cls.handleref.tag, filters)
