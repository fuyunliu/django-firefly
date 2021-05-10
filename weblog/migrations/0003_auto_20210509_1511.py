# Generated by Django 3.2 on 2021-05-09 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weblog', '0002_auto_20210508_2357'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='topic',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
    ]