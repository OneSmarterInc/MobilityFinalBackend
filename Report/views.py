from django.shortcuts import render
from django.shortcuts import render, HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework import permissions
from authenticate.views import saveuserlog
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import UploadBAN, BaseDataTable
from .ser import OrganizationShowSerializer, VendorShowSerializer, showBanSerializer
from .ser import saveBilledSerializer
from .models import Report_Billed_Data, Report_Unbilled_Data
import pandas as pd
from OnBoard.Ban.models import UniquePdfDataTable
from datetime import datetime
from .ser import showBilledReport, showUnbilledReport
from django.db.models.functions import TruncMonth

class GetReportDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if request.user.designation.name == 'Admin':
            orgs = OrganizationShowSerializer(Organizations.objects.filter(company=request.user.company), many=True)
            vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
            bans = showBanSerializer(BaseDataTable.objects.filter(company=request.user.company, viewuploaded=None, viewpapered=None), many=True)
        else:
            orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
            vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
            bans = showBanSerializer(BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None), many=True)

        return Response(
            {
                "orgs": orgs.data,
                "vendors": vendors.data,
                "bans": bans.data,
            },
            status=status.HTTP_200_OK,
        )
