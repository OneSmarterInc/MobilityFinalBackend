# Generated by Django 5.1.4 on 2025-04-22 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0098_organizations_address_organizations_city'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizations',
            name='Zip',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
