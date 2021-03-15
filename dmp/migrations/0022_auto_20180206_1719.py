# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-02-06 17:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmp', '0021_auto_20170803_1518'),
    ]

    operations = [
        migrations.AddField(
            model_name='grant',
            name='grant_value',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='helpscout_url',
            field=models.URLField(blank=True, null=True, verbose_name=b'Helpscout URL'),
        ),
    ]