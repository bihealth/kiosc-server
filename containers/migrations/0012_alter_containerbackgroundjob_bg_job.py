# Generated by Django 4.2.16 on 2024-10-23 15:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("bgjobs", "0001_squashed_0006_auto_20200526_1657"),
        ("containers", "0011_alter_container_container_path"),
    ]

    operations = [
        migrations.AlterField(
            model_name="containerbackgroundjob",
            name="bg_job",
            field=models.ForeignKey(
                help_text="Background job for state etc.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_related",
                to="bgjobs.backgroundjob",
            ),
        ),
    ]
