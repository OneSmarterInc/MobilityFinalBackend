# Generated by Django 5.1.4 on 2025-03-18 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0075_remove_basedatatable_account_charges_credits_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='basedatatable',
            name='item_category',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='basedatatable',
            name='item_description',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
    ]
