# Generated by Django 5.1.4 on 2025-06-18 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('View', '0014_paperbill_unique_paperbill'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paperbill',
            name='bill_date',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='paperbill',
            name='due_date',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
