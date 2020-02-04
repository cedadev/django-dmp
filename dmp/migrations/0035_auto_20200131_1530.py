# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2020-01-31 15:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmp', '0034_project_project_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='project_status',
            field=models.CharField(blank=True, choices=[(b'InitialContact', b'Initial contact'), (b'DMPComms', b'DMP comms'), (b'Progress', b'Progress'), (b'DataDelivery', b'Data delivery')], max_length=200, null=True),
        ),
    ]