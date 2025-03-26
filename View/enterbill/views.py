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
from checkbill import prove_bill_ID

from ..models import viewPaperBill
class PaperBillView(APIView):
    
    permission_classes = [IsAuthenticated]

    def __init__(self):
        self.filtered_baseline = None

    def get(self, request, *args, **kwargs):
        orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
        vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
        bans = showBanSerializer(UploadBAN.objects.all(), many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.all(), many=True)
        paperbills = viewPaperBillserializer(viewPaperBill.objects.filter(company=request.user.company), many=True) if request.user.company else viewPaperBillserializer(viewPaperBill.objects.all(), many=True)
        if request.GET:
            org = request.GET.get('org')
            vendor = request.GET.get('ven')
            ban = request.GET.get('ban')
            invoice_number = request.GET.get('invoicenumber')
            billdate = request.GET.get('billdate')
            duedate = request.GET.get('duedate')
            print(org, vendor, ban, invoice_number, billdate, duedate)
            base = BaseDataTable.objects.filter(sub_company=org, vendor=vendor, accountnumber=ban, invoicenumber=invoice_number)
            if not base.exists():
                return Response({"message": f"No data found for invoice {invoice_number}"}, status=status.HTTP_404_NOT_FOUND)
            baseline = BaselineDataTable.objects.filter(banOnboarded=base[0].banOnboarded).filter(is_draft=False, is_pending=False)
            self.filtered_baseline = BaselineDataTableShowSerializer(baseline, many=True).data
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "bans":bans.data, "data":paperbills.data, "onborded": onboarded.data, "filtered_baseline": self.filtered_baseline},
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
        
        try:
            obj = BaselineDataTable.objects.filter(id=pk)
        except BaselineDataTable.DoesNotExist:
            return Response({"message": "Baseline Data not found"}, status=status.HTTP_404_NOT_FOUND)
        obj = obj[0]
        action = request.GET.get('action') or request.data.get('action')
        if action == "update-category":
            cat = request.data.get('category')
            print(cat)
            obj.category_object = cat
        elif action == "is_draft":
            obj.is_draft = True
            obj.is_pending = False
        elif action == "is_pending":
            obj.is_draft = False
            obj.is_pending = True
        else:
            return Response({"message": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        obj.save()
        saveuserlog(
            request.user,
            f"Baseline with account number {obj.account_number} and invoice number {obj.Wireless_number} Updated with Action: {action}"
        )
        return Response({"message": "Baseline updated successfully"}, status=status.HTTP_200_OK)
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
        cat = BaselineDataTable.objects.all()[1]
        print(cat.category_object)
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "bans":bans.data, "baseline":baselineData.data, "onborded":onboarded.data},
            status=status.HTTP_200_OK,
        )
    def post(self, request, *args, **kwargs):
        pass
    def put(self, request, pk, *args, **kwargs):
        
        try:
            obj = BaselineDataTable.objects.filter(id=pk)
        except BaselineDataTable.DoesNotExist:
            return Response({"message": "Baseline Data not found"}, status=status.HTTP_404_NOT_FOUND)
        obj = obj[0]
        action = request.GET.get('action') or request.data.get('action')
        if action == "update-category":
            cat = request.data.get('category')
            print(cat)
            obj.category_object = cat
        elif action == "is_draft":
            obj.is_draft = True
            obj.is_pending = False
        elif action == "is_pending":
            obj.is_draft = False
            obj.is_pending = True
        else:
            return Response({"message": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        obj.save()
        saveuserlog(
            request.user,
            f"Baseline with account number {obj.account_number} and invoice number {obj.Wireless_number} Updated with Action: {action}"
        )
        return Response({"message": "Baseline updated successfully"}, status=status.HTTP_200_OK)
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
        
        try:
            obj = BaselineDataTable.objects.filter(id=pk)
        except BaselineDataTable.DoesNotExist:
            return Response({"message": "Baseline Data not found"}, status=status.HTTP_404_NOT_FOUND)
        obj = obj[0]
        action = request.GET.get('action') or request.data.get('action')
        if action == "update-category":
            cat = request.data.get('category')
            print(cat)
            obj.category_object = cat
        elif action == "is_draft":
            obj.is_draft = True
            obj.is_pending = False
        elif action == "is_pending":
            obj.is_draft = False
            obj.is_pending = True
        else:
            return Response({"message": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        obj.save()
        saveuserlog(
            request.user,
            f"Baseline with account number {obj.account_number} and invoice number {obj.Wireless_number} Updated with Action: {action}"
        )
        return Response({"message": "Baseline updated successfully"}, status=status.HTTP_200_OK)

    def delete(self, request, pk, *args, **kwargs):
        pass

from ..models import ViewUploadBill
from OnBoard.Ban.models import MappingObjectBan
import ast
import pdfplumber
from OnBoard.Ban.views import ProcessZip
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
            
            if file.name.endswith('.pdf'):
                check = prove_bill_ID(vendor_name=request.data.get('vendor'), bill_path=file)
                if not check:
                    return Response({"message" : f"the uploaded file is not {request.data.get('vendor')} file!"}, status=status.HTTP_400_BAD_REQUEST)
            
            company = request.data.get('company')
            org = request.data.get('sub_company')
            vendor = request.data.get('vendor')
            ban = request.data.get('ban')
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
                ban=ban
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
            if str(file.name).endswith('.pdf'):
                buffer_data = json.dumps({'pdf_path': obj.file.path,'vendor_name': obj.vendor.name if obj.vendor else None,'pdf_filename':obj.file.name,'company_name':obj.company.Company_name,'sub_company_name':obj.organization.Organization_name if obj.organization else None,'types':obj.types})
                process_view_bills.delay(buffer_data, obj.id)
            if (str(file.name).endswith('.xls') or str(file.name).endswith('.xlsx')):
                map = request.data.pop('mappingobj', None)[0]
                map = map.replace('null', 'None')
                map = ast.literal_eval(map)
                for key, value in map.items():
                    if value == "" or value == '':
                        map[key] = None
                mobj = MappingObjectBan.objects.create(viewupload=obj, **map)
                mobj.save()
            if str(file.name).endswith('.zip'):
                addon = ProcessZip(obj)
                check = addon.startprocess()
                print(check)
                if check['error'] == -1:
                    return Response(
                        {"message": f"Problem to add onbaord data, {str(check['message'])}"}, status=status.HTTP_400_BAD_REQUEST
                    )
            saveuserlog(
                request.user,
                f"Uploading file with account number {obj.account_number} and invoice number {obj.Wireless_number}"
            )
            return Response(
                {"message": "File upload is in progress \n It will take some time. "},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, pk, *args, **kwargs):
        pass
    def delete(self, request, pk, *args, **kwargs):
        pass

import json
# from .tasks import process_view_bills
from View.enterbill.tasks import process_view_bills
import re
class ProcessPdf:
    def __init__(self, user_mail, instance, **kwargs):
        print(instance)
        self.instance = instance
        self.file = instance.file
        if self.file is None:
            return {'message' : 'File not found', 'error' : -1}
        self.path = self.file.path
        self.org = instance.organization
        self.company = instance.organization.company
        self.vendor = instance.vendor
        self.email = user_mail
        self.month = instance.month
        self.year = instance.year
        self.account_number = instance.ban
    def startprocess(self):
        print("start process")
        if self.org:
                self.org = self.org.Organization_name
        else:
            return {'message' : 'Organization not found', 'error' : -1}
        if self.company:
            self.company = self.company.Company_name
        else:
            return {'message' : 'Company not found', 'error' : -1}
        if self.vendor:
            self.vendor = self.vendor.name
        else:
            return {'message' : 'Vendor not found', 'error' : -1}

        if self.entrytype:
            self.entrytype = self.entrytype.name
        else:
            return {'message' : 'Entry Type not found', 'error' : -1}
        acc_info = None
        bill_date_info = None
        if 'mobile' in str(self.vendor).lower():
            pass
        elif 'verizon' in str(self.vendor).lower():
            accounts = []
            dates = []
            duration = []
            bill_date = []
            with pdfplumber.open(self.path) as pdf:
                for page_number in range(2):
                    page = pdf.pages[page_number]
                    text = page.extract_text()
                    lines = text.split('\n')
                    for index, line in enumerate(lines):
                        if line.startswith('InvoiceNumber AccountNumber DateDue'):
                            line = lines[index + 1]
                            items = line.split()
                            del items[3]
                            del items[4]
                            del items[3]
                            date = items[2]
                            account = items[1]
                            dates.append(date)
                            accounts.append(account)

                    match = re.search(r'Quick Bill Summary (\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s*-\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b)', text)
                    if match:
                        phone_number = match.group(1)
                        duration.append(phone_number)

                    match = re.search(r'Bill Date (January|February|March|April|May|June|July|August|September|October|November|December) (\d{2}), (\d{4})', text)
                    if match:
                        phone_number = match.group(1)
                        amount = match.group(2)
                        pay = match.group(3)
                        bill_date.append({
                            "phone_number": phone_number,
                            "amount": amount,
                            "pay": pay
                        })

            bill_date1 = [f"{info['phone_number']} {info['amount']} {info['pay']}" for info in bill_date]
            acc_info = accounts[0]
            bill_date_info = bill_date1[0]
        else:
            pages_data = []
            with pdfplumber.open(self.path) as pdf:
                num_of_pages = len(pdf.pages)
            if num_of_pages < 999:
                with pdfplumber.open(self.path) as pdf:
                    pages_data = [page.extract_text() for page in pdf.pages[:2]]

                for page_data in pages_data:
                    first_page_data = page_data
                    break

                first_page_data_dict = {
                    "bill_cycle_date": None,
                    "account_number": None
                }

                for line in first_page_data.splitlines():
                    if line.startswith("Issue Date:"):
                        first_page_data_dict["bill_cycle_date"] = line.split(": ")[-1]
                    elif "Account number:" in line:
                        first_page_data_dict["account_number"] = line.split(": ")[-1]
                acc_info = first_page_data_dict["account_number"]
                bill_date_info = first_page_data_dict["bill_cycle_date"]

        acc_no = acc_info
        bill_date_pdf = bill_date_info
        print(acc_no, bill_date_pdf)

        print(acc_no, self.org, self.company)
        acc_exists  = BaseDataTable.objects.filter(accountnumber=acc_no, sub_company=self.org,company=self.company)
        print(acc_exists)
        # bill_date_exists = PdfDataTable.objects.filter(Bill_Date=bill_date_pdf)
        if acc_exists.exists():
            message = f'Account Number {acc_no}  already exists.'
            print(message)
            return {'message': message, 'error': 1}
        # storage = FileSystemStorage(location='uploaded_contracts/')
        # filename = storage.save(self.file.name, self.path)
        # path = storage.path(filename)

        return {
            'message': 'Process Done',
            'error': 0,
        }
