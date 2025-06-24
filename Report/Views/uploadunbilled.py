from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework import permissions
from authenticate.views import saveuserlog
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import  BaseDataTable
from ..ser import OrganizationShowSerializer, VendorShowSerializer, showBanSerializer
from ..models import  Report_Unbilled_Data
import pandas as pd
from OnBoard.Ban.models import UniquePdfDataTable
from datetime import datetime
from ..ser import showUnbilledReport

class UploadUnbilledReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_year = datetime.now().year
        self.report_type = "Unbilled_Data_Usage"

    def get(self, request, *args, **kwargs):
        print("Get Unbilled Data Usage Report")
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
        filtered_data = Report_Unbilled_Data.objects.filter(**filter_kwargs)
        unique_dates = {}
        for row in filtered_data:
            if row.Date not in unique_dates:
                unique_dates[row.Date] = row
        unique_rows = list(unique_dates.values())
        self.data = showUnbilledReport(unique_rows, many=True)
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
        if report_type != self.report_type:
            return Response({"message": "Invalid report type"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            date = data['date']
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
                month_start = datetime(date.year, date.month, 1)
                week_number = (date - month_start).days // 7 + 1
            except ValueError:
                return Response({"message": "Invalid date format. Expected format is YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                    file_format = 'csv'
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                    file_format = 'xlsx'
                elif file.name.endswith('.txt'):
                    df = pd.read_csv(file, delimiter='\t')
                    file_format = 'txt'
                else:
                    return Response({"message": "Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            for _, row in df.iterrows():
                user_name = row.get('User name', '')
                wireless_number = row.get('Wireless number', '')
                data_usage_gb = row.get('Data Usage (GB)', None)

                if data_usage_gb is None:
                    data_usage_kb = row.get('Data Usage (KB)', None)
                    if data_usage_kb is not None:
                        data_usage_gb = data_usage_kb / 1024 / 1024  # Convert KB to GB

                if user_name and wireless_number and data_usage_gb is not None:
                    # Retrieve device and upgrade eligibility date from unique_pdf_data_table
                    unique_data = UniquePdfDataTable.objects.filter(wireless_number=wireless_number).first()
                    if unique_data:
                        device = unique_data.mobile_device
                        upgrade_eligibility_date = unique_data.upgrade_eligible_date
                    else:
                        device = 'NA'
                        upgrade_eligibility_date = 'NA'

                    # Check if the record already exists
                    record_exists = Report_Unbilled_Data.objects.filter(
                        company=company,
                        organization=org,
                        vendor=vendor,
                        Account_Number=account_number,
                        Wireless_Number=wireless_number,
                        User_Name=user_name,
                        Report_Type=report_type,
                        Month=month,
                        Date=date,
                    ).exists()

                    if record_exists:
                        return Response({"message": "Report Unbilled Data with provided details already exists"}, status=status.HTTP_409_CONFLICT)

                    # Create the new record
                    Report_Unbilled_Data.objects.create(
                        company=company,
                        organization=org,
                        vendor=vendor,
                        Account_Number=account_number,
                        Wireless_Number=wireless_number,
                        User_Name=user_name,
                        Report_Type=report_type,
                        Month=month,
                        Date=date,
                        Week=week_number,
                        Usage=data_usage_gb,
                        Device=device,
                        Upgrade_Eligibilty_Date=upgrade_eligibility_date,
                        File=file,
                        File_Format=file, 
                        Year=str(self.current_year)
                    )
            saveuserlog(
                    request.user, 
                    f"Unbilled Data Usage Report uploaded of file  {file.name} and Vendor: {vendor.name}"
                )
            return Response({
                "message": "Unbilled Data Usage Report uploaded successfully",
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request,pk, *args, **kwargs):
        self.com = None
        self.org = None
        self.vendor = None
        self.account_number = None
        self.month = None
        self.year = None
        self.report_type = self.report_type
        try:
            obj1 = Report_Unbilled_Data.objects.filter(id=pk)
            self.com = obj1[0].company.Company_name
            self.org = obj1[0].organization.Organization_name
            self.vendor = obj1[0].vendor.name
            self.account_number = obj1[0].Account_Number
            self.month = obj1[0].Month
            self.year = obj1[0].Year
            self.report_type = obj1[0].Report_Type
            allobjs = Report_Unbilled_Data.objects.filter(
                company=obj1[0].company,
                organization=obj1[0].organization,
                vendor=obj1[0].vendor,
                Report_Type = obj1[0].Report_Type,
                Account_Number=obj1[0].Account_Number,
                Month=obj1[0].Month,
                Year=obj1[0].Year,
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