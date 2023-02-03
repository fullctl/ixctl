# Generated by Django 3.2.8 on 2021-10-20 12:39

import django.core.validators
import django_inet.models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("django_ixctl", "0007_auto_20211006_1311"),
    ]

    operations = [
        migrations.RenameField(
            model_name="internetexchangemember",
            old_name="as_macro",
            new_name="as_macro_override",
        ),
        migrations.AlterField(
            model_name="routeserver",
            name="asn",
            field=django_inet.models.ASNField(
                help_text="ASN",
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MinValueValidator(0),
                ],
            ),
        ),
    ]
