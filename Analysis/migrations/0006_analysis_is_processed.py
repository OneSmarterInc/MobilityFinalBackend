# Generated by Django 5.1.4 on 2025-04-03 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Analysis', '0005_alter_analysis_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='analysis',
            name='is_processed',
            field=models.BooleanField(default=False),
        ),
    ]
