# Generated by Django 3.2.11 on 2022-04-14 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('containers', '0010_container_container_ip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='container',
            name='container_path',
            field=models.CharField(blank=True, default='', help_text='Path segment of the container URL', max_length=512),
        ),
    ]
