from rest_framework import serializers
from OnBoard.Ban.models import BatchReport, BaseDataTable
from OnBoard.Organization.models import Organizations
from .models import Notification

class BatchReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchReport
        fields = '__all__'
    
class OrganizationShowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name']

class BaseDataSerializer(serializers.ModelSerializer):
    is_bill_in_batch = serializers.SerializerMethodField()
    is_bill_approved = serializers.SerializerMethodField()
    is_bill_payment_done = serializers.SerializerMethodField()
    is_paper_bill = serializers.SerializerMethodField()
    class Meta:
        model = BaseDataTable
        fields = '__all__'
    def get_is_bill_in_batch(self,obj):
        return obj.is_baseline_approved
    def get_is_bill_approved(self,obj):
        return "approved" in obj.batch_approved.lower() if obj.batch_approved else False
    def get_is_bill_payment_done(self,obj):
        return obj.Check.lower() not in ("", None, "null", "false") if obj.Check else False
    def get_is_paper_bill(self,obj):
        return obj.viewpapered is not None
    
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "company", "description", "created_at"]

class NotificationSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"