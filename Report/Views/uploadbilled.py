from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework import permissions
from authenticate.views import saveuserlog
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import BaseDataTable
from ..ser import OrganizationShowSerializer, VendorShowSerializer, showBanSerializer
from ..models import Report_Billed_Data
import pandas as pd
from ..ser import showBilledReport
from datetime import datetime
class UploadBilledReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.report_type = "Billed_Data_Usage"
        self.current_year = datetime.now().year

    def get(self, request, *args, **kwargs):
        print("Upload report Billed!")
        if request.user.designation.name == 'Admin':
            orgs = OrganizationShowSerializer(Organizations.objects.filter(company=request.user.company), many=True)
            vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
            bans = showBanSerializer(BaseDataTable.objects.filter(company=request.user.company, viewuploaded=None, viewpapered=None), many=True)
        else:
            orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
            vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
            bans = showBanSerializer(BaseDataTable.objects.filter(company=request.user.company, viewuploaded=None, viewpapered=None), many=True)
        company = Company.objects.get(Company_name=request.user.company.Company_name) if request.user.company else None
        filter_kwargs = {}
        if company:
            filter_kwargs['company'] = company
        filter_kwargs['Report_Type'] = self.report_type
        filtered_data = Report_Billed_Data.objects.filter(**filter_kwargs)
        unique_dates = {}
        for row in filtered_data:
            if row.Month not in unique_dates:
                unique_dates[row.Month] = row
        unique_rows = list(unique_dates.values())
        self.data = showBilledReport(unique_rows, many=True)
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "bans":bans.data, "data":self.data.data if self.data else None},
            status=status.HTTP_200_OK,
        )
    def post(self, request, *args, **kwargs):
        data = request.data
        org = Organizations.objects.filter(Organization_name=data['sub_company'])[0]
        company = Company.objects.filter(Company_name=org.company.Company_name)[0]
        vendor = Vendors.objects.filter(name=data['vendor'])[0]
        file = data['file']
        account_number = data['account_number']
        month = data['month']
        report_type = data['report_type']
        if report_type == 'Billed_Data_Usage':
            try:
                try:
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file)
                    elif file.name.endswith('.xlsx'):
                        df = pd.read_excel(file)
                    elif file.name.endswith('.txt'):
                        df = pd.read_csv(file, delimiter='\t')
                    else:
                        return Response({"message": "Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:

                    return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                column_mappings = {
                    'Wireless Number': 'wireless_number',
                    'User Name': 'user_name',
                    'Voice Plan Usage': 'voice_plan_usage',
                    'Messaging Usage': 'messaging_usage',
                    'Data Usage (GB)': 'data_usage_gb',
                    'Data Usage (KB)': 'data_usage_kb',
                    'Data Usage (MB)': 'data_usage_mb',
                    'Bill Cycle Date': 'Bill_Cycle_Date '
                }
                actual_columns = df.columns.tolist()
                mapped_columns = {v: k for k, v in column_mappings.items() if k in actual_columns}
                required_columns = ['wireless_number', 'user_name', 'voice_plan_usage', 'messaging_usage','Bill_Cycle_Date ']
                if not all(col in mapped_columns for col in required_columns):
                    return Response({"message": "File is missing required columns"}, status=status.HTTP_200_OK)

                data_usage_column = mapped_columns.get('data_usage_gb')
                if not data_usage_column:
                    data_usage_column = mapped_columns.get('data_usage_kb') or mapped_columns.get('data_usage_mb')

                if not data_usage_column:
                    return Response({"message": "File is missing data usage columns"}, status=status.HTTP_200_OK)

                # Extract necessary data
                existing_data = Report_Billed_Data.objects.filter(
                    company=company,
                    organization=org,
                    vendor=vendor,
                    Account_Number=account_number,
                    Month=month,
                    Year=str(self.current_year)
                ).exists()

                if existing_data:
                    return Response(
                        {"message": "Report Billed Data with provided details already exists"},
                        status=status.HTTP_409_CONFLICT,
                    )
                for _, row in df.iterrows():
                    wireless_number = row.get(mapped_columns['wireless_number'], '')
                    user_name = row.get(mapped_columns['user_name'], '')
                    Bill_Cycle_Date = row.get(mapped_columns['Bill_Cycle_Date '], '')
                    voice_plan_usage = row.get(mapped_columns['voice_plan_usage'], '')
                    messaging_usage = row.get(mapped_columns['messaging_usage'], '')
                    data_usage_gb = row.get(mapped_columns.get('data_usage_gb'), None)
                    data_usage_kb = row.get(mapped_columns.get('data_usage_kb'), None)
                    data_usage_mb = row.get(mapped_columns.get('data_usage_mb'), None)

                    if data_usage_gb is None and data_usage_kb is not None:
                        data_usage_gb = data_usage_kb / 1024 / 1024  # Convert KB to GB
                    elif data_usage_gb is None and data_usage_mb is not None:
                        data_usage_gb = data_usage_mb / 1024  # Convert MB to GB

                    # if data_usage_gb is None:
                        # data_usage_gb = 0  # Handle cases where data usage columns are missing or empty

                    if wireless_number and user_name:
                        Report_Billed_Data.objects.create(
                            company=company,
                            organization=org,
                            vendor=vendor,
                            Account_Number=account_number,
                            Wireless_Number=wireless_number,
                            User_Name=user_name,
                            Report_Type=report_type,
                            Month=month,
                            Voice_Plan_Usage=voice_plan_usage,
                            Messaging_Usage=messaging_usage,
                            Data_Usage_GB=data_usage_gb,
                            File=file,
                            Bill_Cycle_Date = Bill_Cycle_Date,
                            Year=str(self.current_year)  
                        )
                saveuserlog(
                        request.user, 
                        f"Billed Data Usage Report uploaded of file {file.name} and Vendor: {vendor.name}"
                    )
                return Response({
                    "message": "Billed Data Usage Report uploaded successfully",
                }, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Invalid report type"}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk, *args, **kwargs):
        self.com = None
        self.org = None
        self.vendor = None
        self.account_number = None
        self.month = None
        self.year = None
        self.report_type = self.report_type
        try:
            obj1 = Report_Billed_Data.objects.filter(id=pk)
            self.com = obj1[0].company.Company_name
            self.org = obj1[0].organization.Organization_name
            self.vendor = obj1[0].vendor.name
            self.account_number = obj1[0].Account_Number
            self.month = obj1[0].Month
            self.year = obj1[0].Year
            allobjs = Report_Billed_Data.objects.filter(
                company=obj1[0].company,
                organization=obj1[0].organization,
                vendor=obj1[0].vendor,
                Report_Type = obj1[0].Report_Type,
                Month = obj1[0].Month,
                Year=obj1[0].Year,
                Account_Number=obj1[0].Account_Number,
            )
            try:
                allobjs.delete()
            except Exception as e:
                print(e)
                return Response({"message": "Error while deleting related records"}, status=status.HTTP_400_BAD_REQUEST)
            saveuserlog(
                request.user, 
                f"{self.report_type} report attributions company:{self.com}, organization:{self.org}, vendor:{self.vendor}, month:{self.month}, year:{self.year}. account number:{self.account_number}, month:{self.month}, and year:{self.year} deleted successfully."
            )
            return Response({"message": f"{self.report_type} Report deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)