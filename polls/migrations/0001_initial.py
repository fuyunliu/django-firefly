# Generated by Django 3.2 on 2021-05-28 11:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=64, verbose_name='标题')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('choice_num', models.IntegerField(choices=[(1, '单选'), (2, '最多2项'), (3, '最多3项'), (4, '最多4项'), (5, '最多5项'), (6, '最多6项'), (7, '最多7项'), (8, '最多8项'), (9, '最多9项'), (10, '最多10项')], default=1, verbose_name='选项数量')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to=settings.AUTH_USER_MODEL, verbose_name='发布者')),
            ],
            options={
                'verbose_name': '问题',
                'verbose_name_plural': '问题',
                'ordering': ['id'],
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=64, verbose_name='标题')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='polls.question', verbose_name='问题')),
            ],
            options={
                'verbose_name': '选项',
                'verbose_name_plural': '选项',
                'ordering': ['id'],
                'get_latest_by': 'id',
            },
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='polls.choice', verbose_name='选项')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='polls.question', verbose_name='问题')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '投票',
                'verbose_name_plural': '投票',
                'ordering': ['id'],
                'get_latest_by': 'id',
                'unique_together': {('user', 'question', 'choice')},
            },
        ),
    ]
