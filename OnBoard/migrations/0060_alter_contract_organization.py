# Generated by Django 5.1.4 on 2025-03-04 07:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0059_contract'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='organization',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contracts', to='OnBoard.organizations'),
        ),
    ]
