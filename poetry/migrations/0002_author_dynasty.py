# Generated by Django 3.2 on 2021-05-29 16:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poetry', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='dynasty',
            field=models.CharField(default='', max_length=64, verbose_name='朝代'),
            preserve_default=False,
        ),
    ]
