# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-11-24 17:33
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dmp', '0003_auto_20161124_1728'),
    ]

    operations = [
        migrations.AlterField(
            model_name='note',
            name='creator',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]