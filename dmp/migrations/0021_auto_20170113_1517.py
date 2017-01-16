# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-01-13 15:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dmp', '0020_merge_20170113_1513'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='oauthtoken',
            name='user',
        ),
        migrations.AlterField(
            model_name='project',
            name='desc',
            field=models.TextField(blank=True, null=True, verbose_name=b'Description'),
        ),
        migrations.AlterField(
            model_name='project',
            name='other_dataCentres',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name=b'Other Datacentres'),
        ),
        migrations.AlterField(
            model_name='project',
            name='primary_dataCentre',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name=b'Primary Datacentre'),
        ),
        migrations.DeleteModel(
            name='OAuthToken',
        ),
    ]
