# Generated by Django 5.1.4 on 2025-02-12 13:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0025_rename_billingname_basedatatable_billing_name_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pdfdatatable',
            old_name='account_number',
            new_name='accountnumber',
        ),
    ]
