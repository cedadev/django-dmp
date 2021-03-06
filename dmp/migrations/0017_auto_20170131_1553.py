# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-31 15:53
from __future__ import unicode_literals

from django.db import migrations, models
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dmp', '0016_auto_20161223_1419'),
    ]

    operations = [
        migrations.CreateModel(
            name='GrantFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_contents', picklefield.fields.PickledObjectField(editable=False)),
                ('added', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AlterField(
            model_name='project',
            name='ODMP_URL',
            field=models.URLField(blank=True, help_text=b'Outline DMP URL autogenerated when using grant uploader, essentially a best guess. Edit as necessary.', null=True),
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
    ]
