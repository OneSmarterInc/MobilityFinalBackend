# Generated by Django 5.1.4 on 2025-02-28 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0045_alter_uploadban_masteraccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadban',
            name='contract_file',
            field=models.FileField(null=True, upload_to='ban-contracts/'),
        ),
    ]
