# Generated by Django 5.1.4 on 2025-02-27 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0042_alter_location_site_name_location_unique_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadban',
            name='remarks',
            field=models.CharField(blank=True, max_length=2550, null=True),
        ),
    ]
