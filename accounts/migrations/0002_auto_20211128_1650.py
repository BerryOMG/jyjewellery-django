# Generated by Django 3.1 on 2021-11-28 16:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='account',
            old_name='data_joined',
            new_name='date_joined',
        ),
    ]
