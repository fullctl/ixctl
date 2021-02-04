import django_peeringdb.models.concrete as pdb_models
from dal import autocomplete
from django import forms
from django.utils.translation import gettext as _


class ImportIXForm(forms.Form):
    pdb_id = forms.ModelChoiceField(
        label=_("PeeringDB Exchange"),
        queryset=pdb_models.InternetExchange.objects.filter(status="ok"),
        widget=autocomplete.ModelSelect2(url="/ix/autocomplete/pdb/ix"),
    )
