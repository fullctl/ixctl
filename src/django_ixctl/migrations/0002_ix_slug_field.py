# Generated by Django 2.2.17 on 2021-01-19 20:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_ixctl", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="internetexchange",
            name="slug",
            field=models.SlugField(blank=True, max_length=64),
        ),
        migrations.AddConstraint(
            model_name="internetexchange",
            constraint=models.UniqueConstraint(
                fields=("instance", "slug"), name="unique_slug_instance_pair"
            ),
        ),
    ]
