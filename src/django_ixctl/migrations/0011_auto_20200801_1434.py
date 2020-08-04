# Generated by Django 2.2.14 on 2020-08-01 14:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("django_ixctl", "0010_auto_20200801_1429"),
    ]

    operations = [
        migrations.AlterField(
            model_name="routeserverconfig",
            name="rs",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="django_ixctl.Routeserver",
            ),
        ),
    ]