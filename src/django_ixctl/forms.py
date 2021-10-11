from dal import autocomplete
from django import forms
from django.utils.translation import gettext as _


class ImportIXForm(forms.Form):
    pdb_id = forms.IntegerField(
        label=_("PeeringDB Exchange"),
        widget=autocomplete.ModelSelect2(url="/ix/autocomplete/pdb/ix"),
    )
