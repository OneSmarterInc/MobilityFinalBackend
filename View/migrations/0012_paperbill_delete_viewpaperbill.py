# Generated by Django 5.1.4 on 2025-06-18 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('View', '0011_viewuploadbill_ban'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaperBill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sub_company', models.CharField(max_length=255)),
                ('vendor', models.CharField(max_length=255)),
                ('account_number', models.CharField(max_length=255)),
                ('invoice_number', models.CharField(blank=True, max_length=255, null=True)),
                ('bill_date', models.CharField(blank=True, max_length=255, null=True)),
                ('due_date', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'PaperBill',
            },
        ),
        migrations.DeleteModel(
            name='viewPaperBill',
        ),
    ]
