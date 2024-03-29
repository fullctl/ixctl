# Generated by Django 3.2.12 on 2022-07-11 12:20

import django.core.validators
import django.db.models.deletion
import django_inet.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_ixctl", "0010_auto_20211021_1256"),
    ]

    operations = [
        migrations.RenameField(
            model_name="routeserverconfig",
            old_name="rs",
            new_name="routeserver",
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
        migrations.AlterField(
            model_name="routeserverconfig",
            name="task",
            field=models.ForeignKey(
                blank=True,
                help_text="Reference to most recent generate task for this routeserver_config object",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="routeserver_config_set",
                to="django_ixctl.rsconfgenerate",
            ),
        ),
    ]
