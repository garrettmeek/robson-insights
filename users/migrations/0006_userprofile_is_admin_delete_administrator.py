# Generated by Django 5.1 on 2024-09-25 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_userprofile_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.DeleteModel(
            name='Administrator',
        ),
    ]
