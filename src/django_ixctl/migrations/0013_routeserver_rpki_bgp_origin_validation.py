# Generated by Django 2.2.15 on 2020-08-06 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_ixctl", "0012_auto_20200801_1503"),
    ]

    operations = [
        migrations.AddField(
            model_name="routeserver",
            name="rpki_bgp_origin_validation",
            field=models.BooleanField(default=False),
        ),
    ]