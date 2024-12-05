# Generated by Django 4.2.16 on 2024-11-28 04:29

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_remove_entry_group_entry_groups_alter_filter_groups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='classification',
            field=models.CharField(choices=[('1', 'Group 1'), ('2', 'Group 2'), ('3', 'Group 3'), ('4', 'Group 4'), ('5.1', 'Group 5.1'), ('5.2', 'Group 5.2'), ('6', 'Group 6'), ('7', 'Group 7'), ('8', 'Group 8'), ('9', 'Group 9'), ('10', 'Group 10')], max_length=100),
        ),
        migrations.AlterField(
            model_name='entry',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
