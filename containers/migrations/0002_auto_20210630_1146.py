# Generated by Django 3.1.8 on 2021-06-30 09:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('containers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='container',
            name='environment',
            field=models.JSONField(blank=True, help_text='The environment variables to use', null=True),
        ),
    ]
