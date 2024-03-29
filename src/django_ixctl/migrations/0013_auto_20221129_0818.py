# Generated by Django 3.2.15 on 2022-11-29 08:18

import django.core.validators
import django_inet.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_ixctl", "0012_unique_routserver_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="internetexchangemember",
            name="md5",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="routeserver",
            name="asn",
            field=django_inet.models.ASNField(
                help_text="ASN",
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
    ]
