# Generated by Django 2.2.17 on 2021-03-15 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmp', '0027_auto_20201126_1500'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='migrated',
            field=models.BooleanField(default=False),
        ),
    ]