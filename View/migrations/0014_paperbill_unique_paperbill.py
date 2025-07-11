# Generated by Django 5.1.4 on 2025-06-18 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('View', '0013_alter_paperbill_bill_date_alter_paperbill_due_date'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='paperbill',
            constraint=models.UniqueConstraint(fields=('sub_company', 'vendor', 'account_number', 'bill_date'), name='unique_paperbill'),
        ),
    ]
