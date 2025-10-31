# app/analytics/serializers.py
from rest_framework import serializers
from OnBoard.Ban.models import BaseDataTable
from .utils import parse_money, parse_date

class BillSerializer(serializers.ModelSerializer):
    total_charges_num = serializers.SerializerMethodField()
    total_amount_due_num = serializers.SerializerMethodField()
    bill_date_parsed = serializers.SerializerMethodField()
    date_due_parsed = serializers.SerializerMethodField()

    class Meta:
        model = BaseDataTable
        fields = [
            "id","company","sub_company","vendor","vendor_alias","accountnumber",
            "invoicenumber","bill_date","date_due","month","year",
            "total_charges","Total_Amount_Due","batch_approved","banstatus",
            "BillingCurrency","paymentType","billstatus","is_baseline_approved",
            "bill_date_parsed","date_due_parsed","total_charges_num","total_amount_due_num",
        ]

    def get_total_charges_num(self, obj):
        return str(parse_money(obj.total_charges))

    def get_total_amount_due_num(self, obj):
        return str(parse_money(obj.Total_Amount_Due))

    def get_bill_date_parsed(self, obj):
        d = parse_date(obj.bill_date) or parse_date(obj.BillingDate)
        return d.isoformat() if d else None

    def get_date_due_parsed(self, obj):
        d = parse_date(obj.date_due)
        return d.isoformat() if d else None
