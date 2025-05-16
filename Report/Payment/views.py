from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable, BaselineDataTable
from .ser import BaseDataTableShowSerializer, baselinedataserializer, OrganizationShowOnboardSerializer, CompanyShowOnboardSerializer
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company


class GetPaymentReportByDueDate(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        self.data = None
    def get(self, request, *args, **kwargs):
        if request.user.designation.name == "Superadmin":
            all_companys = CompanyShowOnboardSerializer(Company.objects.all(), many=True)
        else:
            all_companys = OrganizationShowOnboardSerializer(Organizations.objects.filter(company=request.user.company), many=True)
        all_accounts = BaseDataTableShowSerializer(BaseDataTable.objects.filter(viewuploaded=None), many=True)
        if 'request_type' in request.GET:
            due_date = request.GET.get('due_date')
            company = request.GET.get('company')
            sub_company = request.GET.get('sub_company')
            vendor = request.GET.get('vendor')
            ban = request.GET.get('ban')

            print(due_date, company, sub_company, vendor, ban)

            # if not due_date:
            #     return Response({"message": "due_date is required in yyyy-mm-dd format"}, status=status.HTTP_400_BAD_REQUEST)
            if due_date:
                try:
                    formatted_due_date = datetime.strptime(due_date, "%Y-%m-%d").strftime("%m/%d/%Y")
                except ValueError:
                    return Response({"message": "Invalid date format. Expected yyyy-mm-dd."}, status=status.HTTP_400_BAD_REQUEST)

            queryset = BaseDataTable.objects.filter(banOnboarded=None,banUploaded=None)

            if company:
                queryset = queryset.filter(company=company)
                if not queryset.exists():
                    return Response({"message": f"No data found for the given company {company}"}, status=status.HTTP_404_NOT_FOUND)
            if sub_company:
                queryset = queryset.filter(sub_company=sub_company)
                if not queryset.exists():
                    return Response({"message": f"No data found for the given sub_company {sub_company}"}, status=status.HTTP_404_NOT_FOUND)
            if vendor:
                queryset = queryset.filter(vendor=vendor)
                if not queryset.exists():
                    return Response({"message": f"No data found for the given vendor {vendor}"}, status=status.HTTP_404_NOT_FOUND)
            if ban:
                queryset = queryset.filter(accountnumber=ban)
                if not queryset.exists():
                    return Response({"message": f"No data found for the given ban {ban}"}, status=status.HTTP_404_NOT_FOUND)
            if due_date:
                queryset = queryset.filter(date_due=formatted_due_date)
                if not queryset.exists():
                    return Response({"message": f"No data found for the given due_date {due_date}"}, status=status.HTTP_404_NOT_FOUND)

            self.data = [{**obj, 'due_date': due_date} for obj in baselinedataserializer(BaselineDataTable.objects.filter(viewuploaded=queryset[0].viewuploaded), many=True).data]
        return Response({"data": self.data, "orgs":all_companys.data, "bans":all_accounts.data}, status=status.HTTP_200_OK)

