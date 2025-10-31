from rest_framework import serializers
from OnBoard.Location.models import Location

from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable
class OrganizationLocationSerializer(serializers.ModelSerializer):
    company = serializers.CharField()
    organization = serializers.CharField()
    division = serializers.CharField()
    class Meta:
        model = Location
        exclude = ("location_picture_1", "location_picture_2","location_picture_3","location_picture_4", "created", "updated")

from datetime import datetime
from dateutil import parser
class InventorySerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    gl_code = serializers.SerializerMethodField()
    banstatus = serializers.SerializerMethodField()
    passed_count = serializers.SerializerMethodField()
    today_count = serializers.SerializerMethodField()

    class Meta:
        model = UniquePdfDataTable
        fields = (
            "company", "sub_company", "vendor", "account_number", "wireless_number",
            "location", "gl_code", "banstatus", "user_name", "plans",
            "User_status", "upgrade_eligible_date",
            "passed_count", "today_count"
        )

    # --------------- Internal helper ---------------
    def _filterObj(self, obj):
        return BaseDataTable.objects.filter(
            banUploaded=obj.banUploaded,
            banOnboarded=obj.banOnboarded
        ).first()

    # --------------- Existing computed fields ---------------
    def get_location(self, wireless):
        loc = self._filterObj(wireless)
        return loc.location if loc else ""

    def get_gl_code(self, wireless):
        glcode = self._filterObj(wireless)
        return glcode.GlCode if glcode else ""

    def get_banstatus(self, wireless):
        bs = self._filterObj(wireless)
        return bs.banstatus if bs else ""

    # --------------- Count cache logic ---------------
    def _get_upgrade_summary(self, wireless):
        """
        Compute or fetch cached passed/today counts per BAN.
        Uses dateutil.parser for flexible date parsing.
        """
        cache_key = f"{wireless.banUploaded}-{wireless.banOnboarded}"
        if not hasattr(self, "_upgrade_summary_cache"):
            self._upgrade_summary_cache = {}

        if cache_key in self._upgrade_summary_cache:
            return self._upgrade_summary_cache[cache_key]

        all_users = UniquePdfDataTable.objects.filter(
            banUploaded=wireless.banUploaded,
            banOnboarded=wireless.banOnboarded
        ).exclude(upgrade_eligible_date__isnull=True).exclude(upgrade_eligible_date='')

        today = datetime.today().date()
        passed_count, today_count = 0, 0

        for user in all_users:
            try:
                date_str = user.upgrade_eligible_date.strip()
                date_obj = parser.parse(date_str, fuzzy=True).date()

                if date_obj < today:
                    passed_count += 1
                elif date_obj == today:
                    today_count += 1

            except Exception:
                # skip invalid or unparsable dates
                continue

        summary = {"passed_count": passed_count, "today_count": today_count}
        self._upgrade_summary_cache[cache_key] = summary
        return summary

    # --------------- New fields using cached summary ---------------
    def get_passed_count(self, wireless):
        return self._get_upgrade_summary(wireless)["passed_count"]

    def get_today_count(self, wireless):
        return self._get_upgrade_summary(wireless)["today_count"]
    
    