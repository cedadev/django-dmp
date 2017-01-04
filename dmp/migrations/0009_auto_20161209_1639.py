# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-12-09 16:39
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dmp', '0008_auto_20161130_1422'),
    ]

    operations = [
        migrations.CreateModel(
            name='Emailtemplates',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_name', models.CharField(max_length=200)),
                ('last_edited', models.DateField(auto_now_add=True)),
                ('content', models.TextField(blank=True)),
                ('edited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='metadataform',
            name='form_type',
            field=models.CharField(blank=True, choices=[(b'projectForm', b'Project Form'), (b'instrumentForm', b'Instrument Form'), (b'datasetForm', b'Dataset Form'), (b'platformForm', b'Platform Form')], max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='metadataform',
            name='modified',
            field=models.DateTimeField(auto_now_add=True, verbose_name=b'last modified'),
        ),
        migrations.AlterField(
            model_name='note',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dmp.Person'),
        ),
        migrations.AlterField(
            model_name='project',
            name='dmp_agreed',
            field=models.DateField(blank=True, help_text=b'Date format dd/mm/yyyy', null=True, verbose_name=b'DMP Agreed'),
        ),
        migrations.AlterField(
            model_name='project',
            name='enddate',
            field=models.DateField(blank=True, help_text=b'Date format dd/mm/yyyy', null=True, verbose_name=b'End Date'),
        ),
        migrations.AlterField(
            model_name='project',
            name='initial_contact',
            field=models.DateField(blank=True, help_text=b'Date format dd/mm/yyyy', null=True, verbose_name=b'Initial Contact'),
        ),
        migrations.AlterField(
            model_name='project',
            name='startdate',
            field=models.DateField(blank=True, help_text=b'Date format dd/mm/yyyy', null=True, verbose_name=b'Start Date'),
        ),
    ]