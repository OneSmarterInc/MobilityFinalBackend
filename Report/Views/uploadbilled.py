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
import json
from Batch.views import create_notification
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

        # --- Basic validations ---
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

        if not file or not mapping:
            return Response(
                {"message": "File and mapping are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if report_type != "Billed_Data_Usage":
            return Response(
                {"message": "Unsupported report type"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Read file ---
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.name.endswith(".xlsx"):
                df = pd.read_excel(file)
            elif file.name.endswith(".txt"):
                df = pd.read_csv(file, delimiter="\t")
            else:
                return Response(
                    {"message": "Unsupported file format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception:
            return Response(
                {"message": "Unable to read uploaded file"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ---- Normalize ----
        df.columns = [c.strip() for c in df.columns]
        mapping = {k.strip(): v.strip() for k, v in mapping.items()}

        df = df.rename(columns=mapping)
        print(mapping, df.columns)
        required_fields = [
            "Wireless_Number",
            "User_Name",
            "Voice_Plan_Usage",
            "Messaging_Usage",
            "Bill_Cycle_Date",
        ]

        missing = [f for f in required_fields if f not in df.columns]
        if missing:
            return Response(
                {"message": f"Missing required mappings: {missing}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Validate duplicate report ---
        if Report_Billed_Data.objects.filter(
            company=company,
            organization=org,
            vendor=vendor,
            Account_Number=account_number,
            Month=month,
            Year=str(self.current_year),
        ).exists():
            return Response(
                {"message": "Report already exists for given details"},
                status=status.HTTP_409_CONFLICT,
            )

        # --- Data cleaning ---
        wn_format = r'^(\d{3}-\d{3}-\d{4}|\d{3}\.\d{3}\.\d{4}|\(\d{3}\)[ -]?\d{3}-\d{4})$'
        df = df[df["Wireless_Number"].astype(str).str.match(wn_format, na=False)]

        # --- Process rows ---
        for _, row in df.iterrows():
            wireless_number = row["Wireless_Number"]
            user_name = row["User_Name"]

            if not wireless_number or not user_name:
                continue

            data_usage_gb = row.get("Data_Usage_GB")
            data_usage_mb = row.get("Data_Usage_MB")
            data_usage_kb = row.get("Data_Usage_KB")

            if pd.isna(data_usage_gb):
                if not pd.isna(data_usage_mb):
                    data_usage_gb = data_usage_mb / 1024
                elif not pd.isna(data_usage_kb):
                    data_usage_gb = data_usage_kb / 1024 / 1024

            Report_Billed_Data.objects.create(
                company=company,
                organization=org,
                vendor=vendor,
                Account_Number=account_number,
                Wireless_Number=wireless_number,
                User_Name=user_name,
                Report_Type=report_type,
                Month=month,
                Year=str(self.current_year),
                Voice_Plan_Usage=row["Voice_Plan_Usage"],
                Messaging_Usage=row["Messaging_Usage"],
                Data_Usage_GB=data_usage_gb,
                Bill_Cycle_Date=row["Bill_Cycle_Date"],
                File=file,
            )

        create_notification(
            request.user,
            f"Billed Data Usage Report uploaded: {file.name} (Vendor: {vendor.name})",
            request.user.company,
        )

        saveuserlog(
            request.user,
            f"Billed Data Usage Report uploaded: {file.name} (Vendor: {vendor.name})",
        )

        return Response(
            {"message": "Billed Data Usage Report uploaded successfully"},
            status=status.HTTP_200_OK,
        )
    
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
            create_notification(
                request.user, 
                f"{self.report_type} report attributions company:{self.com}, organization:{self.org}, vendor:{self.vendor}, month:{self.month}, year:{self.year}. account number:{self.account_number}, month:{self.month}, and year:{self.year} deleted successfully.", request.user.company
            )
            return Response({"message": f"{self.report_type} Report deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message": "Unable to delete report."}, status=status.HTTP_400_BAD_REQUEST)