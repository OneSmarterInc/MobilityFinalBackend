# Generated by Django 5.1.4 on 2025-05-03 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0115_alter_basedatatable_billingadd_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basedatatable',
            name='banstatus',
            field=models.CharField(blank=True, default='Active', max_length=255, null=True),
        ),
    ]
