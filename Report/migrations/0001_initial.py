# Generated by Django 5.1.4 on 2025-03-08 12:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Dashboard', '0005_billtype'),
        ('OnBoard', '0067_batchreport_output_file_alter_batchreport_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report_Billed_Data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Account_Number', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Wireless_Number', models.CharField(blank=True, default='', max_length=20, null=True)),
                ('User_Name', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Report_Type', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Month', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Year', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Voice_Plan_Usage', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Messaging_Usage', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Data_Usage_GB', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('File', models.FileField(blank=True, null=True, upload_to='BilledData/')),
                ('Bill_Cycle_Date', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('created', models.DateTimeField(auto_now=True)),
                ('updated', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='OnBoard.company')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='OnBoard.organizations')),
                ('vendor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Dashboard.vendors')),
            ],
            options={
                'db_table': 'ReportBilledData',
            },
        ),
        migrations.CreateModel(
            name='Report_Unbilled_Data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Account_Number', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Wireless_Number', models.CharField(blank=True, default='', max_length=20, null=True)),
                ('User_Name', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Report_Type', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Month', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Year', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Week', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Date', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Usage', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Device', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('Upgrade_Eligibilty_Date', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('File', models.FileField(blank=True, null=True, upload_to='UnbilledData/')),
                ('File_Format', models.CharField(blank=True, max_length=10, null=True)),
                ('created', models.DateTimeField(auto_now=True)),
                ('updated', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='OnBoard.company')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='OnBoard.organizations')),
                ('vendor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Dashboard.vendors')),
            ],
            options={
                'db_table': 'ReportUnbilledData',
            },
        ),
    ]
