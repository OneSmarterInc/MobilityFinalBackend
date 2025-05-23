# Generated by Django 5.1.4 on 2025-04-15 07:12

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0088_remove_basedatatable_created_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='basedatatable',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='basedatatable',
            name='updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
