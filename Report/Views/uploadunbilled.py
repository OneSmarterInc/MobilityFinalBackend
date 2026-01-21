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
import json
from Batch.views import create_notification
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

        try:
            org = Organizations.objects.get(Organization_name=data["sub_company"])
            company = org.company
            vendor = Vendors.objects.get(name=data["vendor"])
        except (Organizations.DoesNotExist, Vendors.DoesNotExist):
            return Response(
                {"message": "Invalid organization or vendor"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file = data.get("file")
        mapping = data.get("mapping")
        mapping = json.loads(mapping) if isinstance(mapping, str) else mapping
        account_number = data.get("account_number")
        month = data.get("month")
        report_type = data.get("report_type")
        date_str = data.get("date")

        if report_type != self.report_type:
            return Response({"message": "Invalid report type"}, status=400)

        if not file or not mapping or not date_str:
            return Response(
                {"message": "File, mapping, and date are required"},
                status=400,
            )

        # ---- Parse date ----
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            month_start = datetime(date.year, date.month, 1)
            week_number = (date - month_start).days // 7 + 1
        except ValueError:
            return Response(
                {"message": "Invalid date format. Expected YYYY-MM-DD"},
                status=400,
            )

        # ---- Read file ----
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.name.endswith(".xlsx"):
                df = pd.read_excel(file)
            elif file.name.endswith(".txt"):
                df = pd.read_csv(file, delimiter="\t")
            else:
                return Response({"message": "Unsupported file format"}, status=400)
        except Exception:
            return Response({"message": "Unable to read file"}, status=400)

        # ---- Normalize ----
        df.columns = [c.strip() for c in df.columns]
        mapping = {k.strip(): v.strip() for k, v in mapping.items()}
        df = df.rename(columns=mapping)

        required = ["Wireless_Number", "User_Name", "Usage"]
        missing = [r for r in required if r not in df.columns]
        if missing:
            return Response(
                {"message": f"Missing required mappings: {missing}"},
                status=400,
            )

        # ---- Duplicate report check (ONCE) ----
        if Report_Unbilled_Data.objects.filter(
            company=company,
            organization=org,
            vendor=vendor,
            Account_Number=account_number,
            Month=month,
            Date=date,
            Year=str(self.current_year),
        ).exists():
            return Response(
                {"message": "Report already exists for given details"},
                status=status.HTTP_409_CONFLICT,
            )

        # ---- Filter valid wireless numbers ----
        wn_format = r'^(\d{3}-\d{3}-\d{4}|\d{3}\.\d{3}\.\d{4}|\(\d{3}\)[ -]?\d{3}-\d{4})$'
        df = df[df["Wireless_Number"].astype(str).str.match(wn_format, na=False)]

        # ---- Process rows ----
        for _, row in df.iterrows():
            wireless = row["Wireless_Number"]
            user = row["User_Name"]
            usage_gb = row["Usage"]

            if pd.isna(usage_gb):
                continue

            unique = UniquePdfDataTable.objects.filter(
                wireless_number=wireless
            ).only("mobile_device", "upgrade_eligible_date").first()

            Report_Unbilled_Data.objects.create(
                company=company,
                organization=org,
                vendor=vendor,
                Account_Number=account_number,
                Wireless_Number=wireless,
                User_Name=user,
                Report_Type=report_type,
                Month=month,
                Date=date,
                Week=week_number,
                Usage=usage_gb,
                Device=unique.mobile_device if unique else "NA",
                Upgrade_Eligibilty_Date=unique.upgrade_eligible_date if unique else None,
                File=file,
                File_Format=file.name.split(".")[-1],
                Year=str(self.current_year),
            )

        saveuserlog(
            request.user,
            f"Unbilled Data Usage Report uploaded: {file.name} (Vendor: {vendor.name})",
        )

        return Response(
            {"message": "Unbilled Data Usage Report uploaded successfully"},
            status=200,
        )

        
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
            # create_notification(
            #     request.user, 
            #     f"{self.report_type} report attributions company:{self.com}, organization:{self.org}, vendor:{self.vendor}, month:{self.month}, year:{self.year}. account number:{self.account_number}, month:{self.month}, and year:{self.year} deleted successfully.", request.user.company
            # )
            return Response({"message": f"{self.report_type} Report deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message": "Unable to delete report."}, status=status.HTTP_400_BAD_REQUEST)