# Generated by Django 5.1.4 on 2025-03-26 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('View', '0010_alter_contracts_contract_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='viewuploadbill',
            name='ban',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
