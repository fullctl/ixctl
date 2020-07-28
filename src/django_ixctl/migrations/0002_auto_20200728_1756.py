# Generated by Django 2.2.14 on 2020-07-28 17:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_ixctl', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='internetexchange',
            name='pdb_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='internetexchange',
            name='pdb_version',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='internetexchangemember',
            name='ix',
            field=models.ForeignKey(help_text='Members at this Exchange', on_delete=django.db.models.deletion.CASCADE, related_name='member_set', to='django_ixctl.InternetExchange'),
        ),
    ]