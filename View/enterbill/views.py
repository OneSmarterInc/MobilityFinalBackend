from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable, BaselineDataTable
from .ser import OrganizationShowSerializer, VendorShowSerializer, showBanSerializer, BaselineDataTableShowSerializer, viewPaperBillserializer, showOnboardedSerializer
from Dashboard.ModelsByPage.DashAdmin import Vendors, PaymentType
from ..models import viewPaperBill


from ..models import viewPaperBill
class PaperBillView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
        vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
        bans = showBanSerializer(UploadBAN.objects.all(), many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.all(), many=True)
        paperbills = viewPaperBillserializer(viewPaperBill.objects.filter(company=request.user.company), many=True) if request.user.company else viewPaperBillserializer(viewPaperBill.objects.all(), many=True)
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "bans":bans.data, "data":paperbills.data, "onborded": onboarded.data},
            status=status.HTTP_200_OK,
        )
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            print(data)

            company = data.get('company')
            org = data.get('organization')
            vendor = data.get('vendor')
            if str(company).lower() in (None, 'null', ''):
                company = None
            else:
                company = Company.objects.filter(Company_name=company)[0]

            obj = viewPaperBill.objects.create(
                company = company,
                organization = Organizations.objects.filter(Organization_name=org)[0],
                vendor = Vendors.objects.filter(name=vendor)[0],
                account_number = data.get('account_number'),
                invoice_number = data.get('invoice_number'),
                invoice_date = data.get('invoice_date'),
                due_date = data.get('due_date')
            )
            obj.save()
            saveuserlog(
                request.user,
                f"Paper Bill with Account Number: {data.get('account_number')}, Invoice Number: {data.get('invoice_number')} Uploaded"
            )
            return Response(
                {"message": "paper bill uploaded successfully"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(e)
            return Response(
                {"message": f"Error Occured while Uploading Paper Bill: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
            )
       

    def put(self, request, pk, *args, **kwargs):
        pass
    def delete(self, request, pk, *args, **kwargs):
        pass

class PendingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
        vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
        bans = showBanSerializer(UploadBAN.objects.all(), many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.all(), many=True)

        baselineData = BaselineDataTableShowSerializer(BaselineDataTable.objects.all(), many=True)
        cat = BaselineDataTable.objects.all()[45]
        print(cat.category_object)
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "bans":bans.data, "baseline":baselineData.data, "onborded":onboarded.data},
            status=status.HTTP_200_OK,
        )
    def post(self, request, *args, **kwargs):
        pass
    def put(self, request, pk, *args, **kwargs):
        pass
    def delete(self, request, pk, *args, **kwargs):
        pass

class DraftView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
        vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
        bans = showBanSerializer(UploadBAN.objects.all(), many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.all(), many=True)
        baselineData = BaselineDataTableShowSerializer(BaselineDataTable.objects.all(), many=True)

        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "bans":bans.data, "baseline":baselineData.data, "onborded":onboarded.data},
            status=status.HTTP_200_OK,
        )
    def post(self, request, *args, **kwargs):
        pass
    def put(self, request, pk, *args, **kwargs):
        pass
    def delete(self, request, pk, *args, **kwargs):
        pass

from ..models import ViewUploadBill
from OnBoard.Ban.models import MappingObjectBan
import ast
import pdfplumber

class UploadfileView(APIView):
    permission_classes = [IsAuthenticated]

    def check_tmobile_type(self, Billpath):
        Lines = []
        with pdfplumber.open(Billpath) as pdf:
            for i, page in enumerate(pdf.pages):
                if i == 0:
                    page_text = page.extract_text()
                    lines = page_text.split('\n')
                    Lines.extend(lines)
                else:
                    break

        if 'Bill period Account Invoice Page' in Lines[0]:
            print("Type1 : Bill period Account Invoice Page")
            return 2
        elif 'Your Statement' in Lines[0]:
            print("Type2 : Your Statement")
            return 1
        else:
            None
    def get(self, request, *args, **kwargs):
        orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
        vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
        bans = showBanSerializer(UploadBAN.objects.all(), many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.all(), many=True)

        baselineData = BaselineDataTableShowSerializer(BaselineDataTable.objects.all(), many=True)

        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "bans":bans.data, "baseline":baselineData.data, "onborded":onboarded.data},
            status=status.HTTP_200_OK,
        )
    def post(self, request, *args, **kwargs):
        try:
            file = request.data.get('file')
            filetype = str(file.name).split('.')[-1]
            if filetype not in ['pdf', 'xls', 'xlsx', 'zip']:
                return Response({"message": "Invalid file type"}, status=status.HTTP_400_BAD_REQUEST)
            if filetype in ['xls', 'xlsx']:
                filetype = 'excel'
            company = request.data.get('company')
            org = request.data.get('sub_company')
            vendor = request.data.get('vendor')
            month  = request.data.get('month')
            year  = request.data.get('year')
            print(filetype, company, org, vendor, month, year)
            if str(company).lower() in (None, 'null', ''):
                company = None
            else:
                company = Company.objects.filter(Company_name=company)[0]
            obj = ViewUploadBill.objects.create(
                file_type = filetype,
                file = file,
                company = company,
                organization = Organizations.objects.filter(Organization_name=org)[0],
                vendor = Vendors.objects.filter(name=vendor)[0],
                month = month,
                year = year,
            )
            obj.save()

            if 'mobile' in str(obj.vendor.name):
                check_type = self.check_tmobile_type(obj.file.path)
                if check_type == 1:
                    obj.types = 'first'
                elif check_type == 2:
                    obj.types ='second'
                else:
                    obj.types = None
            saveuserlog(
                request.user,
                f"Uploaded File: {file.name} in ViewUploadBill model",
            )
            if str(file.name).endswith('.pdf'):
                process = ProcessPdf(obj)
                start = process.process()
                if start['error'] == 1:
                    print(start)
                    return Response({"message": f"Error in processing pdf file {start['message']}"}, status=status.HTTP_400_BAD_REQUEST)
            if (str(file.name).endswith('.xls') or str(file.name).endswith('.xlsx')):
                mapping_obj = request.data.get('mappingobj')
                map = request.data.pop('mappingobj', None)[0]
                map = map.replace('null', 'None')
                map = ast.literal_eval(map)
                for key, value in map.items():
                    if value == "" or value == '':
                        map[key] = None
                mobj = MappingObjectBan.objects.create(viewupload=obj, **map)
                mobj.save()
            if str(file.name).endswith('.zip'):
                pass
            return Response(
                {"message": "File uploaded successfully"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, pk, *args, **kwargs):
        pass
    def delete(self, request, pk, *args, **kwargs):
        pass

import json
from .tasks import process_view_bills

class ProcessPdf:
    def __init__(self, instance):
        self.instance = instance
        self.vendor = instance.vendor
        self.company = instance.company
        self.organization = instance.organization
        self.month = instance.month
        self.year = instance.year
        self.file = instance.file
        self.types = instance.types
        print(self.instance)

    def process(self):
        try:
            if self.company:
                self.company = self.company.Company_name
            else:
                self.company = None
            if self.vendor:
                self.vendor = self.vendor.name
            else:
                self.vendor = None
            if self.organization:
                self.organization = self.organization.Organization_name
            else:
                self.organization = None
        except Exception as e:
            print(f"Error occurred while processing PDF: {str(e)}")
            return {"message": f"Error occurred while processing PDF {str(e)}", "error":1}
        try:
            buffer_data = json.dumps({'pdf_path': self.file.path,'vendor_name': self.vendor,'pdf_filename':self.file.name,'company_name':self.company,'sub_company_name':self.organization,'types':self.types})
            process_view_bills(buffer_data, self.instance)
            print("process ends...")
            return {"message": "File processed successfully in background", "error":0}
        except Exception as e:
            print(f"Error occurred while processing PDF in background: {str(e)}")
            return {"message": f"Error occurred while processing PDF in background: {str(e)}", "error":1}
