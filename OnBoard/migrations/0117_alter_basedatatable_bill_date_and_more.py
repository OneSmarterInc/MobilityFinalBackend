# Generated by Django 5.1.4 on 2025-05-03 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0116_alter_basedatatable_banstatus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basedatatable',
            name='bill_date',
            field=models.DateField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='baselinedatatable',
            name='bill_date',
            field=models.DateField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='uniquepdfdatatable',
            name='bill_date',
            field=models.DateField(blank=True, max_length=255, null=True),
        ),
    ]
