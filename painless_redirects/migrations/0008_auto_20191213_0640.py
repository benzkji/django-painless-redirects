# -*- coding: utf-8 -*-
# Generated by Django 1.11.26 on 2019-12-13 06:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('painless_redirects', '0007_auto_20181107_0207'),
    ]

    operations = [
        migrations.AddField(
            model_name='redirect',
            name='auto_created',
            field=models.BooleanField(default=False, editable=False, help_text='Created by a 404 hit? (must be enabled via settings)', verbose_name='Auto created'),
        ),
        migrations.AddField(
            model_name='redirect',
            name='hits',
            field=models.IntegerField(default=0, editable=False),
        ),
    ]
