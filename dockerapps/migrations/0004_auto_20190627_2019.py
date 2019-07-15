# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-27 18:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("dockerapps", "0003_auto_20190627_1943")]

    operations = [
        migrations.AlterField(
            model_name="containerlogentry",
            name="process",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="log_entries",
                to="dockerapps.DockerProcess",
            ),
        ),
        migrations.AlterField(
            model_name="imagelogentry",
            name="image",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="log_entries",
                to="dockerapps.DockerImage",
            ),
        ),
    ]
