# Generated by Django 3.2 on 2021-07-12 09:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0004_auto_20210530_1343'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='avatar_hash',
        ),
        migrations.AddField(
            model_name='profile',
            name='view_count',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='浏览量'),
        ),
    ]
