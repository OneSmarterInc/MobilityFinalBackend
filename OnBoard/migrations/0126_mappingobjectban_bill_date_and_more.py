# Generated by Django 5.1.4 on 2025-06-23 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0125_basedatatable_viewpapered_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mappingobjectban',
            name='bill_date',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='mappingobjectban',
            name='invoice_number',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
