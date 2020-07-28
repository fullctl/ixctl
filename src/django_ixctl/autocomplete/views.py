from dal import autocomplete

import django_peeringdb.models.concrete as pdb_models


class peeringdb_ix(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = pdb_models.IXLan.objects.filter(status="ok")
        if self.q:
            qs = qs.filter(ix__name__istartswith=self.q)
        return qs

    def get_result_label(self, ixlan):
        if ixlan.name:
            return "{} - {}".format(ixlan.ix.name, ixlan.name)
        return ixlan.ix.name


class peeringdb_org(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = pdb_models.Organization.objects.filter(status="ok")
        if self.q:
            qs = qs.filter(name__istartswith=self.q)
        return qs
