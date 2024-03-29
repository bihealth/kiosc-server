# Generated by Django 3.1.8 on 2021-07-06 13:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('containertemplates', '0003_auto_20210630_1632'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='containertemplateproject',
            options={'ordering': ('-date_created',)},
        ),
        migrations.AlterModelOptions(
            name='containertemplatesite',
            options={'ordering': ('-date_created',)},
        ),
        migrations.AddField(
            model_name='containertemplateproject',
            name='containertemplatesite',
            field=models.ForeignKey(blank=True, help_text='Link to site-wide container template', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='containertemplateprojects', to='containertemplates.containertemplatesite'),
        ),
    ]
