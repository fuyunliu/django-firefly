# Generated by Django 3.2 on 2021-05-28 13:14

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together={('user', 'choice')},
        ),
        migrations.RemoveField(
            model_name='vote',
            name='question',
        ),
    ]
