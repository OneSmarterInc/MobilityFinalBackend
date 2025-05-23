# Generated by Django 5.1.4 on 2025-02-19 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OnBoard', '0040_uniquepdfdatatable_device_etf_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='cost_centers',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='data_plan_allotment',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='data_plan_charges',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='device_id',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='insurance',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='international_data_feat',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='international_text_feat',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='international_voice_feat',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='mobile_access_charge',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='site_name',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='third_party_app_charge',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='upgrade_eligible_date',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='voice_plan_charges',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='uniquepdfdatatable',
            name='voice_plan_mins',
            field=models.CharField(blank=True, default='NaN', max_length=255, null=True),
        ),
    ]
