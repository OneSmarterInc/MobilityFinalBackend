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
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None), many=True)
        paperbills = viewPaperBillserializer(viewPaperBill.objects.filter(company=request.user.company), many=True) if request.user.company else viewPaperBillserializer(viewPaperBill.objects.all(), many=True)
        if request.GET:
            org = request.GET.get('org')
            vendor = request.GET.get('ven')
            ban = request.GET.get('ban')
            invoice_number = request.GET.get('invoicenumber')
            billdate = request.GET.get('billdate')
            duedate = request.GET.get('duedate')
            base = BaseDataTable.objects.filter(banOnboarded=None,banUploaded=None).filter(sub_company=org, vendor=vendor, accountnumber=ban)
            print(base)
            if invoice_number:
                base = base.filter(invoicenumber=invoice_number)
            if not base.exists():
                return Response({"message": f"No data found for invoice {invoice_number}"}, status=status.HTTP_404_NOT_FOUND)
            baseline = BaselineDataTable.objects.filter(viewuploaded=base[0].viewuploaded, account_number=base[0].accountnumber).filter(is_draft=False, is_pending=False)
            self.filtered_baseline = BaselineDataTableShowSerializer(baseline, many=True).data
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "data":paperbills.data, "onborded": onboarded.data, "filtered_baseline": self.filtered_baseline},
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
            print(company)
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
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None), many=True)

        baselineData = BaselineDataTableShowSerializer(BaselineDataTable.objects.filter(banOnboarded=None,banUploaded=None), many=True)
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "baseline":baselineData.data, "onborded":onboarded.data},
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
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None), many=True)
        baselineData = BaselineDataTableShowSerializer(BaselineDataTable.objects.filter(banOnboarded=None,banUploaded=None), many=True)
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "baseline":baselineData.data, "onborded":onboarded.data},
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
from django.forms.models import model_to_dict

from checkbill import prove_bill_ID
class UploadfileView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        self.processed_data = None

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
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None), many=True)

        baselineData = BaselineDataTableShowSerializer(BaselineDataTable.objects.all(), many=True)

        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "baseline":baselineData.data, "onborded":onboarded.data},
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
            found = ViewUploadBill.objects.filter(
                vendor = Vendors.objects.filter(name=vendor)[0],
                month = month,
                year = year,
                ban=ban
            ).exists()
            if found:
                return Response({"message": f"{vendor} bill already exists for {month}-{year}"}, status=status.HTTP_400_BAD_REQUEST)
            print(filetype, company, org, vendor, month, year, ban)
            if str(company).lower() in (None, 'null', ''):
                company = None
            else:
                company = Company.objects.filter(Company_name=company)[0]

            found = BaseDataTable.objects.filter(sub_company=org, vendor=vendor, accountnumber=ban)
            print(found, len(list(found)))
            if len(list(found)) != 0:
                print("Founded")
                if 'master' in found[0].Entry_type.lower():
                    return Response({
                        "message": f"ban with Master Account is not acceptable!"
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                found = UploadBAN.objects.filter(organization=Organizations.objects.filter(Organization_name=org).first(), Vendor=Vendors.objects.filter(name=vendor).first(), account_number=ban)
                print(found)
                if len(list(found)) != 0:
                    print("Founded")
                    if 'master' in found[0].entryType.name.lower():
                        return Response({
                            "message": f"ban with  Master Account is not acceptable!"
                        })
                else:
                    return Response({"message": f"Ban not found for {org} and {vendor}"}, status=status.HTTP_400_BAD_REQUEST)
            
            found = found[0]
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
                addon = ProcessPdf(instance=obj, user_mail=request.user.email)
                check = addon.startprocess()
                print(check)
                if check['error'] != 0:
                    return Response(
                        {"message": f"Problem to upload file, {str(check['message'])}"}, status=status.HTTP_400_BAD_REQUEST
                    )
                
                buffer_data = json.dumps({'pdf_path': obj.file.path,'vendor_name': obj.vendor.name if obj.vendor else None,'pdf_filename':obj.file.name,'company_name':obj.company.Company_name if obj.company else None,'sub_company_name':obj.organization.Organization_name if obj.organization else None,'types':obj.types})
                print(buffer_data)
                process_view_bills.delay(buffer_data, obj.id)
            elif (str(file.name).endswith('.xls') or str(file.name).endswith('.xlsx')):
                map = request.data.pop('mappingobj', None)[0]
                map = map.replace('null', 'None')
                map = ast.literal_eval(map)
                for key, value in map.items():
                    if value == "" or value == '':
                        map[key] = None
                mobj = MappingObjectBan.objects.create(viewupload=obj, **map)
                mobj.save()
                check = ProcessExcel(instance=obj, user_mail=request.user.email)
                check = check.process()
                if check['error']!= 0:
                    return Response(
                        {"message": f"Problem to process excel data, {str(check['message'])}"}, status=status.HTTP_400_BAD_REQUEST
                    )
                # AllUserLogs.objects.create(
                #     user_email=request.user.email,
                #     description=(
                #         f"User onboarded excel file for {company} - {sub_company} "
                #         f"with account number {Ban} and vendor - {vendor}."
                #     ),
                #     previus_data=json.dumps(previous_data_log) if previous_data_log else "",
                #     new_data=json.dumps(new_data_log) if new_data_log else ""
                # )

                # Send the data to Celery for background processing
                buffer_data = json.dumps({
                    'csv_path': obj.file.path,
                    'company': obj.company.Company_name if obj.company else None,
                    'sub_company': obj.organization.Organization_name if obj.organization else None,
                    'vendor': obj.vendor.name if obj.vendor else None,
                    'account_number': obj.ban,
                    'mapping_json': model_to_dict(MappingObjectBan.objects.get(viewupload=obj)) or {}
                })
                print(buffer_data)
                process_view_excel.delay(buffer_data, obj.id)
            elif str(file.name).endswith('.zip'):
                addon = ProcessZip(obj)
                check = addon.startprocess()
                print(check)
                if check['error'] == -1:
                    return Response(
                        {"message": f"Problem to add onbaord data, {str(check['message'])}"}, status=status.HTTP_400_BAD_REQUEST
                    )
                self.processed_data = BaselineDataTable.objects.filter(viewuploaded=obj)
                self.processed_data = BaselineDataTableShowSerializer(self.processed_data, many=True).data
                with open('results.json', 'w') as file:
                    json.dump(self.processed_data, file)
            else:
                return Response({"message": "Invalid file type"}, status=status.HTTP_400_BAD_REQUEST)
            saveuserlog(
                request.user,
                f"Uploading file if {obj.vendor.name}-{obj.ban} for {obj.month}-{obj.year}"
            )
            return Response(
                {"message": "File uploaded successfully!" if filetype == "zip" else "File upload is in progress \n It will take some time.", "baseline":self.processed_data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
        allobjs = BaselineDataTableShowSerializer(BaselineDataTable.objects.filter(viewuploaded=obj.viewuploaded, is_pending=False, is_draft=False), many=True)
        saveuserlog(
            request.user,
            f"Baseline with account number {obj.account_number} and invoice number {obj.Wireless_number} Updated with Action: {action}"
        )
        return Response({"message": "Baseline updated successfully", "baseline":allobjs.data}, status=status.HTTP_200_OK)
    def delete(self, request, pk, *args, **kwargs):
        pass

import json
# from .tasks import process_view_bills
from View.enterbill.tasks import process_view_bills, process_view_excel
import re
import os
import zipfile
import pandas as pd
from checkbill import check_tmobile_type
from io import StringIO, BytesIO
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
            print()
            with pdfplumber.open(self.path) as pdf:
                for i, page in enumerate(pdf.pages):
                    if i == 0:
                        page_text = page.extract_text()
                        lines = page_text.split('\n')
                        pages_data.extend(lines)
                    else:
                        break
            
            first_page_data_dict = {
                    "bill_cycle_date": None,
                    "account_number": None
                }

            for line in pages_data:
                if line.startswith("Issue Date:"):
                    first_page_data_dict["bill_cycle_date"] = line.split(": ")[-1]
                elif "Account number:" in line:
                    first_page_data_dict["account_number"] = line.split(": ")[-1]
            print(first_page_data_dict)
            acc_info = first_page_data_dict["account_number"]
            bill_date_info = first_page_data_dict["bill_cycle_date"]

                

        acc_no = acc_info
        bill_date_pdf = bill_date_info
        print(acc_no, bill_date_pdf)

        print(acc_no, self.org, self.company)

        if acc_no != self.account_number:
            self.instance.delete()
            return {'message' : f'Account number from the Pdf file did not matched with input ban', 'error' : -1}
        if self.month != str(bill_date_pdf).split(' ')[0] and self.year != str(bill_date_pdf).split(' ')[2]:
            self.instance.delete()
            return {'message' : f'Bill date from the Pdf file did not matched with input month and year', 'error' : -1}
        if BaseDataTable.objects.filter(accountnumber=acc_no, sub_company=self.org, bill_date=bill_date_pdf): 
            self.instance.delete()
            return {'message' : f'The bill with account number {acc_no} and bill date {bill_date_pdf} already exists', 'error' : -1}
        return {
            'message': 'Process Done',
            'error': 0,
        }

class ProcessZip:
    def __init__(self, instance, **kwargs):
        self.instance = instance
        self.path = instance.file
        if not self.path:
            return {'message' : 'File not found', 'error' : -1}
        else:
            self.path = self.path.path
        self.org = instance.organization
        self.company = instance.organization.company
        print(self.company)
        self.vendor = instance.vendor
        self.month = instance.month
        self.masteraccount = instance.ban
        self.year = instance.year
        self.types = None
        self.ban = instance.ban


    def startprocess(self):
        print("start process")
        try:
            if self.org:
                self.org = self.org.Organization_name
            else:
                return {'message' : 'Organization not found', 'error' : -1}
            if self.company:
                self.company = self.company.Company_name
                print("company====", self.company)
            else:
                return {'message' : 'Company not found', 'error' : -1}
            if self.vendor:
                self.vendor = self.vendor.name
            else:
                return {'message' : 'Vendor not found', 'error' : -1}
            if 'mobile' in str(self.vendor).lower():
                self.types = check_tmobile_type(self.path)

            if self.path.endswith('.zip'):
                data_base, data_pdf,detailed_df,required_df = self.extract_rdd_data(self.path,self.org)
                print("in unique=",len(detailed_df))
                data_base['company'] = self.company
                data_base['vendor'] = self.vendor
                data_base['sub_company'] = self.org
                data_base['master_account'] = self.masteraccount
                data_base['Total_Current_Charges'] = list(required_df['Total Current Charges'])[0]
                data_base['Remidence_Address'] = list(required_df['Remittance Address'])[0]
                data_base['Billing_Name'] = list(required_df['Bill Name'])[0]
                data_base['Total_Amount_Due'] = list(required_df['Total Amount Due'])[0]

                v, t = None, None
                category_data = data_pdf.to_dict(orient='records')
                for entry in category_data:
                    entry['company'] = self.company
                    entry['vendor'] = self.vendor
                self.save_to_pdf_data_table(data_pdf, v, t)
                print("saved to pdf data table")

                for entry in data_pdf.to_dict(orient="records"):
                    entry['company'] = self.company
                    entry['vendor'] = self.vendor
                acc_no = data_base['accountnumber']
                bill_date = data_base['bill_date']

                print(acc_no, bill_date)
                
                if acc_no != self.ban:
                    self.instance.delete()
                    return {'message' : f'Account number from the RDD file did not matched with input ban', 'error' : -1}
                if self.month != str(bill_date).split(' ')[0] and self.year != str(bill_date).split(' ')[2]:
                    self.instance.delete()
                    return {'message' : f'Bill date from the RDD file did not matched with input month and year', 'error' : -1}
                from OnBoard.Ban.models import BaseDataTable
                if BaseDataTable.objects.filter(accountnumber=acc_no, company=self.company, sub_company=self.org, bill_date=bill_date).exists():
                    return {'message' : f'Bill already exists for account number {acc_no}', 'error' : -1}
                else:
                    obj = BaseDataTable.objects.create(viewuploaded=self.instance, **data_base)
                    print("saved to base data table")
                    obj.save()
                print('done')
                self.save_to_batch_report(data_base, self.vendor)
                print('saved to batch report')
                self.save_to_unique_pdf_data_table(detailed_df, v, t)
                print('saved to unique pdf data table')
                from collections import defaultdict
                wireless_data = defaultdict(lambda: defaultdict(dict))
                tmp_df = detailed_df
                tmp_df.rename(columns={'Item Category':'Item_Category','Item Description':'Item_Description','Wireless Number':'Wireless_number'},inplace=True)
                for idx, row in tmp_df.iterrows():
                            wireless_number = row['Wireless_number']
                            item_category = row['Item_Category']
                            item_description = row['Item_Description']
                            charges = row['Charges']
                            if pd.notna(item_category) and pd.notna(item_description) and pd.notna(charges):
                                wireless_data[wireless_number][item_category][item_description] = charges
                result_list = [dict(wireless_data)]
                udf = pd.DataFrame(data_pdf)
                wireless_numbers = []
                charges_objects = []
                for entry in result_list:
                        for number, charges in entry.items():
                            wireless_numbers.append(number)
                            charges_objects.append(json.dumps(charges))  # Convert dictionary to JSON string for storage

                    # Create the DataFrame with two columns: Wireless_number and Charges_Object
                obj_df = pd.DataFrame({
                        'Wireless_number': wireless_numbers,
                        'category_object': charges_objects
                    })
                udf.rename(columns={'wireless_number':'Wireless_number'},inplace=True)
                category_obj_df = pd.merge(udf,obj_df,on='Wireless_number',how='left')
                category_obj_df['category_object'] = category_obj_df['category_object'].apply(
                lambda x: {"NAN": "NAN"} if pd.isna(x) or x == '' else x
                )
                category_data = category_obj_df.to_dict(orient='records')
                for entry in category_data:
                    entry['company'] = self.company
                    entry['vendor'] = self.vendor
                self.save_to_baseline_data_table(category_data, self.vendor, self.types)
                print("saved to baseline data table")
                return {'message' : 'RDD uploaded successfully!', 'error' : 1}
        except Exception as e:
            print(f'Error occurred while processing zip file: {str(e)}')
            return {'message' : f'Error occurred while processing zip file: {str(e)}', 'error' : -1}
    
            
    def save_to_baseline_data_table(self, data, vendor, types):
        print("save to baseline data table")
        data_df = pd.DataFrame(data)
        if 'mobile' in str(vendor).lower() and self.types == 1:
        # if ('mobile' in str(vendor).lower()) and (str(types).lower().startswith('f')):
            column_mapping = {
                'Wireless_number': 'wireless_number',
                'Recurring Charges': 'monthly_charges',
                'Usage Charges': 'usage_and_purchase_charges',
                'Other Charges': 'surcharges_and_other_charges_and_credits',
                'Third-party Charges': 'third_party_charges_includes_tax',
                'Taxes & Surcharges': 'taxes_governmental_surcharges_and_fees',
                'Total Current Charges': 'total_charges',
                'Data Usage (KB)': 'data_usage',
                'Data Usage (MB)': 'data_usage',
                'User name': 'user_name',
                'Foundation account': 'foundation_account',
                'item category': 'item_category',
                'item description': 'item_description',
                'bill_date': 'bill_date',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company',
                'category_object':'category_object',
                'account_number':'account_number'
            }

            # Drop any columns not in the mapping
            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            # Rename the columns
            data_df = df_filtered.rename(columns=column_mapping)
        elif 'mobile' in str(vendor).lower() and self.types == 2:
            column_mapping = {
                'Wireless Number': 'wireless_number',
                'User Name': 'user_name',
                'Plans': 'plans',
                'Usage charges': 'usage_and_purchase_charges',
                'Equipment': 'equipment_charges',
                'Taxes & Fees': 'taxes_governmental_surcharges_and_fees',
                'Total': 'total_charges',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company'
            }

            # Drop columns not in the mapping
            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            # Rename the columns based on the mapping
            data_df = df_filtered.rename(columns=column_mapping)
        
        if 'Page Number' in data_df.columns:
            data_df.drop(columns=['Page Number','Monthly charges Add-ons','Billing_Name','Billing_Address', 'Remidence_Addresss','Activity since last bill'],inplace=True)
        data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account Number':'account_number_y','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data_df.columns = data_df.columns.str.replace('&', 'and')
        data_df.columns = data_df.columns.str.replace('-', ' ')
        data_df.columns = data_df.columns.str.replace(' ', '_')
        data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)

        data = data_df.to_dict(orient='records')

        import json
        from OnBoard.Ban.models import BaselineDataTable
        objects_to_create = []

        for item in data:

            # Convert dictionary values to JSON strings where needed
            processed_item = {key: json.dumps(value) if isinstance(value, dict) else value for key, value in item.items()}
            processed_item.pop('company')
            processed_item.pop('vendor')
            
            # Create Django model instance
            objects_to_create.append(BaselineDataTable(viewuploaded=self.instance, **processed_item, company=self.company, vendor=self.vendor))

        # Bulk insert records
        BaselineDataTable.objects.bulk_create(objects_to_create, ignore_conflicts=True)


    def save_to_unique_pdf_data_table(self, data, vendor,types):
        print("save to unique_pdf_data_table")
        data_df = pd.DataFrame(data)
        if 'mobile' in str(vendor).lower() and self.types == 1:
        # if ('mobile' in str(vendor).lower()) and (str(types).lower().startswith('f')):
            column_mapping = {
                'wireless number': 'wireless_number',
                'Recurring Charges': 'monthly_charges',
                'Usage Charges': 'usage_and_purchase_charges',
                'Other Charges': 'surcharges_and_other_charges_and_credits',
                'Third-party Charges': 'third_party_charges_includes_tax',
                'Taxes & Surcharges': 'taxes_governmental_surcharges_and_fees',
                'Total Current Charges': 'total_charges',
                'Data Usage (KB)': 'data_usage',
                'Data Usage (MB)': 'data_usage',
                'User name': 'user_name',
                'Foundation account': 'foundation_account',
                'item category': 'item_category',
                'item description': 'item_description',
                'bill_date': 'bill_date',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company',
                'account_number':'account_number'
            }
            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            # Rename the columns
            data_df = df_filtered.rename(columns=column_mapping)
        elif 'mobile' in str(vendor).lower() and self.types == 2:
            column_mapping = {
                'Wireless Number': 'wireless_number',
                'User Name': 'user_name',
                'Plans': 'plans',
                'Usage charges': 'usage_and_purchase_charges',
                'Equipment': 'equipment_charges',
                'Taxes & Fees': 'taxes_governmental_surcharges_and_fees',
                'Total': 'total_charges',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company'
            }

            # Drop columns not in the mapping
            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            # Rename the columns based on the mapping
            data_df = df_filtered.rename(columns=column_mapping)
        if 'Page Number' in data_df.columns:
            data_df.drop(columns=['Page Number','Monthly charges Add-ons','Billing_Name','Billing_Address', 'Remidence_Addresss','Activity since last bill'],inplace=True)
        data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account Number':'account_number_y','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data_df.columns = data_df.columns.str.replace('&', 'and')
        data_df.columns = data_df.columns.str.replace('-', ' ')
        data_df.columns = data_df.columns.str.replace(' ', '_')
        data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data = data_df.to_dict(orient='records')
        
        from OnBoard.Ban.models import UniquePdfDataTable

        data = self.map_json_to_model(data)
        model_fields = {field.name for field in UniquePdfDataTable._meta.fields}
        objects_to_create = [
            UniquePdfDataTable(viewuploaded=self.instance, **{key: value for key, value in item.items() if key in model_fields})
            for item in data
        ]
        # Bulk insert records
        UniquePdfDataTable.objects.bulk_create(objects_to_create, ignore_conflicts=True)
    def map_json_to_model(self, data):
        KEY_MAPPING = {
            "account_number_y": "account_number",
            "Wireless_Number": "wireless_number",
            "User_Name": "user_name",
            "Item_Description": "plans",
            "Cost_Center": "cost_center",
            "Item_Category": "account_charges_and_credits", 
            "sub_company": "sub_company",
            "Charges": "total_charges",
        }
        mapped_data = []
        for entry in data:
            mapped_entry = {}

            for key, value in entry.items():
                mapped_key = KEY_MAPPING.get(key, key)  
                mapped_entry[mapped_key] = value if pd.notna(value) else "NaN"

            mapped_data.append(mapped_entry)

        return mapped_data
    def save_to_batch_report(self, data, vendor):
        print("save to batch report")
        try:
            if (str(vendor).lower().startswith('a') and str(vendor).endswith('t')):
                return None
            if ('mobile' in str(vendor).lower()):
                temp = data
                temp_fig = data
            else:
                temp = data[0]
                temp_fig = data[0]
            
            bill_date = temp['bill_date']
            from datetime import datetime
            try:
                date_object = datetime.strptime(bill_date, '%B %d %Y')
                formatted_date = date_object.strftime('%m/%d/%Y')
                temp_fig["bill_date"] = formatted_date
            except:
                try:
                    date_obj = datetime.strptime(bill_date, '%b %d, %Y')
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    temp_fig["bill_date"] = formatted_date
                except:
                    temp_fig['bill_date'] = 'NA'
            
            try:
                if temp["Date_Due"] != "Past":
                    date_due = temp["Date_Due"]
                    date_object_short_year = datetime.strptime(date_due, '%m/%d/%y')
                    formatted_date_long_year = date_object_short_year.strftime('%m/%d/%Y')
                    temp_fig["Date_Due"] = formatted_date_long_year
            except:
                temp_fig["Date_Due"] = 'NA'
            
            remittenceAddress = temp['Remidence_Address']
            parts = remittenceAddress.split(',')

            addresscity = parts[0].split(' ')
            address = f"{addresscity[0]} {addresscity[1]} {addresscity[2]}"
            city = addresscity[4]
            temp_fig["Vendor_City"] = city
            statezip = parts[1].strip().split(' ')
            state = statezip[0]
            temp_fig["Vendor_State"] = state
            temp_fig['Remidence_Address'] = address
            zip_code = statezip[1]
            temp_fig["Vendor_Zip"] = zip_code
        
        except:
            if (str(vendor).lower().startswith('a') and str(vendor).endswith('t')):
                temp = data
                temp_fig = data
            else:
                temp = data
                temp_fig = data
            
            bill_date = temp['bill_date']
            try:
                date_object = datetime.strptime(bill_date, '%B %d %Y')
                formatted_date = date_object.strftime('%m/%d/%Y')
                temp_fig['bill_date'] = temp_fig.pop('bill_date')
                temp_fig["bill_date"] = formatted_date
            except:
                try:
                    date_obj = datetime.strptime(bill_date, '%b %d, %Y')
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    temp_fig['bill_date'] = temp_fig.pop('bill_date')
                    temp_fig["bill_date"] = formatted_date
                except:
                    temp_fig['bill_date'] = temp_fig.pop('bill_date')
                    temp_fig['bill_date'] = 'NA'

            try:
                if temp["date_due"] != "Past":
                    date_due = temp["date_due"]
                    date_object_short_year = datetime.strptime(date_due, '%m/%d/%y')
                    formatted_date_long_year = date_object_short_year.strftime('%m/%d/%Y')
                    temp_fig['Date_Due'] = temp_fig.pop('date_due')
                    temp_fig["Date_Due"] = formatted_date_long_year
            except:
                temp_fig['Date_Due'] = temp_fig.pop('date_due')
                temp_fig["Date_Due"] = 'NA'

            temp_fig['AccountNumber'] = temp_fig.pop('accountnumber')
            temp_fig['InvoiceNumber'] = temp_fig.pop('invoicenumber')
            temp_fig['Total_Charges'] = temp_fig.pop('total_charges')
            temp_fig['Remidence_Address'] = 'NA'
            temp_fig['Billing_Name'] = 'NA'
            temp_fig["Vendor_City"] = 'NA'
            temp_fig["Vendor_State"] = 'NA'
            temp_fig["Vendor_Zip"] = 'NA'
        key_mapping = {
            'Date_Due': 'Due_Date',
            'AccountNumber': 'Customer_Vendor_Account_Number',
            'InvoiceNumber': 'Invoice_Number',
            'bill_date': 'Invoice_Date',
            'Remidence_Address': 'Vendor_Address_1',
            'Billing_Name': 'Cust_Id',
            'Total_Charges': 'Net_Amount',
            'vendor': 'Vendor_Name_1',
            'company_name': 'company',
            'Vendor_City': 'Vendor_City',
            'Vendor_State': 'Vendor_State',
            'Vendor_Zip': 'Vendor_Zip'
        }
        fields_to_remove = [
            'Website',
            'Duration',
            'pdf_path',
            'pdf_filename',
            'Billing_Address',
            'Client_Address',
            'foundation_account'
        ]

        for field in fields_to_remove:
            if field in temp_fig:
                del temp_fig[field]

        renamed_data = {key_mapping.get(key, key): value for key, value in temp_fig.items()}

        from OnBoard.Ban.models import BatchReport


        existing_record = BatchReport.objects.filter(
            Customer_Vendor_Account_Number=renamed_data['Customer_Vendor_Account_Number'],
            company=renamed_data['company'],
            Vendor_Name_1=renamed_data['Vendor_Name_1'],
            Invoice_Date=renamed_data['Invoice_Date']
        ).first()

        try:
            batch_vendor = vendor
            if (str(vendor).lower().startswith('a') and str(vendor).endswith('t')):
                batch_vendor = 'ATT'
            elif ('verizon' in str(vendor).lower()):
                batch_vendor = 'VER'
            entered_vendor_zip = zip_code
            entered_vendor_state = state
            entered_vendor_city = city

            count_matches = BatchReport.objects.filter(
                Vendor_Zip=entered_vendor_zip,
                Vendor_State=entered_vendor_state,
                Vendor_City=entered_vendor_city
            )

            result = count_matches.first()

            count_matches = result[0]

            if count_matches > 0:
                max_location_code_entry = (
                    BatchReport.objects
                    .filter(Vendor_Zip=entered_vendor_zip, Vendor_State=entered_vendor_state, Vendor_City=entered_vendor_city)
                    .exclude(Location_Code__isnull=True)  # Exclude null values to avoid errors
                    .order_by('-Location_Code')  # Sorting to get the highest value
                    .values_list('Location_Code', flat=True)  # Get only the Location_Code column
                    .first()
                )

                # Extract the numeric portion after the first three characters
                if max_location_code_entry:
                    max_numeric_part = max_location_code_entry[3:]  # Extract the numeric part
                    new_numeric_part = str(int(max_numeric_part) + 1).zfill(3)  # Increment and pad with leading zeros
                else:
                    new_numeric_part = "001"

                # Generate the new Location_Code
                new_location_code = f"{batch_vendor}{new_numeric_part}"

                # Update records with the new Location_Code
                BatchReport.objects.filter(
                    Vendor_Zip=entered_vendor_zip, Vendor_State=entered_vendor_state, Vendor_City=entered_vendor_city
                ).update(Location_Code=new_location_code)

                print("Location code assigned/updated for the entered vendor-zip:", new_location_code)
            else:
                print("The entered vendor-zip number does not exist in the database.")
        except:
            pass

        # Check if the record exists
        existing_data = BatchReport.objects.filter(
            Customer_Vendor_Account_Number=renamed_data['Customer_Vendor_Account_Number'],
            company=renamed_data['company'],
            Vendor_Name_1=renamed_data['Vendor_Name_1']
        ).first()

        if existing_data:
            # Update existing record
            existing_data.Due_Date = renamed_data['Due_Date']
            existing_data.Invoice_Number = renamed_data['Invoice_Number']
            existing_data.Invoice_Date = renamed_data['Invoice_Date']
            existing_data.Cust_Id = renamed_data['Cust_Id']
            existing_data.Net_Amount = renamed_data['Net_Amount']
            existing_data.save()
        else:
            new_entry = BatchReport.objects.create(viewuploaded=self.instance, **renamed_data)

            if 'new_location_code' in locals() and new_location_code:
                BatchReport.objects.filter(
                    Vendor_Zip=entered_vendor_zip, Vendor_State=entered_vendor_state, Vendor_City=entered_vendor_city
                ).update(Location_Code=new_location_code)

    def save_to_pdf_data_table(self, data, vendor, types):
        print("save to pdf data table")
        data_df = pd.DataFrame(data)
        print('in saves B')
        if 'mobile' in str(vendor).lower() and self.types == 1:
        # if ('mobile' in str(vendor).lower()) and (str(types).lower().startswith('f')):
            column_mapping = {
                'wireless number': 'Wireless_number',
                'User name': 'User_name',
                'Invoice number': 'Group_number',
                'Recurring Charges': 'Monthly_Charges',
                'Usage Charges': 'Usage_and_Purchase_Charges',
                'Other Charges': 'Surcharges_and_Other_Charges_and_Credits',
                'Taxes & Surcharges': 'Taxes_Governmental_Surcharges_and_Fees',
                'Total Current Charges': 'Total_Charges',
                'Data Usage (KB)': 'Data_Usage',
                'item category': 'item_category',
                'item description': 'item_description',
                'Foundation account': 'foundation_account',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company'
            }
            data_df = data_df.rename(columns=column_mapping)
            data_df = data_df[[col for col in data_df.columns if col in column_mapping.values()]]
        elif 'mobile' in str(vendor).lower() and self.types == 2:
            column_mapping = {
                'Wireless Number': 'Wireless_number',
                'User Name': 'User_name',
                'Plans': 'Plans',
                'Usage charges': 'Usage_and_Purchase_Charges',
                'Equipment': 'Equipment_Charges',
                'Taxes & Fees': 'Taxes_Governmental_Surcharges_and_Fees',
                'Total': 'Total_Charges',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company'
            }

            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            data_df = df_filtered.rename(columns=column_mapping)

        if 'Page Number' in data_df.columns:
            data_df.drop(columns=['Page Number','Monthly charges Add-ons','Billing_Name','Billing_Address', 'Remidence_Addresss','Activity since last bill'],inplace=True)
        data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account_number':'Account_number','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data_df.columns = data_df.columns.str.replace('&', 'and')
        data_df.columns = data_df.columns.str.replace('-', ' ')
        data_df.columns = data_df.columns.str.replace(' ', '_')
        data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data = data_df.to_dict(orient='records')
        from OnBoard.Ban.models import PdfDataTable
        for item in data:
            if 'company' in item:
                item.pop('company')
            if 'vendor' in item:
                item.pop('vendor')
            try:
                obj = PdfDataTable.objects.create(viewuploaded=self.instance, **item, company=self.company, vendor=self.vendor)
                obj.save()
            except Exception as e:
                print(f'Error saving to database: {e}')
                return {'error':-1, 'message':f'{str(e)}'}
    
    def save_to_base_data_table(self, data):
        print("save to base data table")
        from OnBoard.Ban.models import BaseDataTable
        objects_to_create = [BaseDataTable(viewuploaded=self.instance, **item) for item in data]

        BaseDataTable.objects.bulk_create(objects_to_create, ignore_conflicts=True)


    def extract_rdd_data(self, filepath, organization):
        print("extract rdd data")
        extract_dir = 'Bills/media/extracted_files'
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipfile:
            return {'message' : 'Invalid zip file', 'error' : -1}
        except Exception as e:
            print("Error extracting rdd data=", str(e))
            return {'message' : str(e), 'error' : -1}
        
        relevant_files = [
            os.path.join(root, file)
            for root, _, files in os.walk(extract_dir)
            for file in files if file.endswith('.txt')
        ]
        for filepath in relevant_files:
            if 'Account & Wireless Summary' in filepath:
                database, datapdf = self.process_desired_file1(filepath, organization)
            elif 'Acct & Wireless Charges Detail Summary' in filepath:
                detailed_df = self.process_desired_file2(filepath, organization)
            elif 'AccountSummary' in filepath:
                required_df = self.process_account_summary(filepath, organization)
        self.cleanup_extracted_files(extract_dir)
        return database, datapdf, detailed_df, required_df
    
    def process_desired_file1(self, filepath, organization):
        print("process desired file 1")
        with open(filepath, 'r') as file:
            file_data = file.read()
            df = pd.read_csv(StringIO(file_data), sep='\t')
            def convert_column_name(column_name):
                return column_name.lower().replace(' ', '_')
            df.columns = df.columns.map(convert_column_name)
            required_columns = ['bill_cycle_date', 'account_number', 'date_due',
            'invoice_number', 'bill_period', 'wireless_number', 'user_name',
            'cost_center', 'your_calling_plan',
            'account_charges_and_credits', 'monthly_charges',
            'usage_and_purchase_charges', 'equipment_charges',
            'total_surcharges_and_other_charges_and_credits',
            'taxes,_governmental_surcharges_and_fees', 'third_party_charges',
            'total_charges','voice_plan_usage', 'messaging_usage']
            required_df = df[required_columns].copy()
            column_mapping = {
                'bill_cycle_date': 'bill_date',
                'bill_period': 'duration',
                'your_calling_plan':'plans',
                'invoice_number':'invoicenumber',
                'account_number':'accountnumber',
                "total_surcharges_and_other_charges_and_credits":"surcharges_and_other_charges_and_credits",
                'taxes,_governmental_surcharges_and_fees':'taxes_governmental_surcharges_and_fees',
                'third_party_charges':'third_party_charges_includes_tax'
            }
            required_df.rename(columns=column_mapping,inplace=True)
            # conn = sqlite3.connect('db.sqlite3')
            base_data_df = required_df.iloc[1][['bill_date', 'accountnumber', 'date_due',
            'invoicenumber', 'duration','total_charges']].copy()
            acc_mapping = {'accountnumber':'account_number'}
            required_df.rename(columns=acc_mapping,inplace=True)
            # base_data_df.to_sql('myapp_base_data_table',conn,if_exists='replace', index=False)
            pdf_data_df = required_df[['account_number','wireless_number','user_name','plans','cost_center',
            'account_charges_and_credits', 'monthly_charges',
            'usage_and_purchase_charges', 'equipment_charges',
            'surcharges_and_other_charges_and_credits',
            'taxes_governmental_surcharges_and_fees', 'third_party_charges_includes_tax',
            'total_charges','voice_plan_usage', 'messaging_usage']].copy()
            # pdf_data_df.to_sql('myapp_pdf_data_table',conn,if_exists='replace', index=False)
            # pdf_data_df.to_sql('myapp_unique_pdf_data_table',conn,if_exists='replace', index=False)
            # conn.close()
            pdf_data_df['sub_company'] = organization
            return base_data_df,pdf_data_df
    
    def process_desired_file2(self, filepath, organization):
        print("process desired file 2")
        with open(filepath, 'r') as file:
            file_data = file.read()
            df = pd.read_csv(StringIO(file_data), sep='\t')
            df.rename(columns={'Cost':'Charges'},inplace=True)
            detailed_df = df
            detailed_df['sub_company'] = organization
            return detailed_df
        
    def process_account_summary(self, filepath, organization):
        print("process account summary")
        with open(filepath, 'r') as file:
            file_data = file.read()
            vdf = pd.read_csv(StringIO(file_data), sep='\t')
            vdf['sub_company'] = organization
            return vdf

    def cleanup_extracted_files(self, directory):
        print("cleanup extracted files")
        for root, dirs, files in os.walk(directory):
            for file in files:
                os.remove(os.path.join(root, file))
        os.rmdir(directory)
    
import tempfile

class ProcessExcel:

    def __init__(self, instance, user_mail):
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
        self.ban = instance.ban
        self.mapping = model_to_dict(MappingObjectBan.objects.filter(viewupload=self.instance)[0])
        


    def process(self):
        try:
            df_csv = pd.read_excel(BytesIO(self.file.read()))
            df_csv.columns = df_csv.columns.str.strip()

            df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

            # Save column names mapping in Column_mapping_data
            columns_list = df_csv.columns.tolist()
            column_names_str = ','.join(columns_list)

            # Save the uploaded file temporarily for background processing
            with tempfile.NamedTemporaryFile(delete=False) as temper_file:
                for chunk in self.file.chunks():
                    temper_file.write(chunk)
                path = temper_file.name

            # Parse the mapping object and set wireless number column
            wireless_column_name = self.mapping.get('wireless_number', 'wireless_number')

            # Filter unique_pdf_data_table for existing data with the given account number (Ban)
            existing_data = UniquePdfDataTable.objects.filter(account_number=self.ban)

            # Create a dictionary of existing data by wireless number for easy access
            existing_wireless_data = {
                row['wireless_number']: row for row in existing_data.values()
            }

            # Initialize logs for previous and new data
            previous_data_log = []
            new_data_log = []

            for _, new_row in df_csv.iterrows():
                wireless_number = new_row.get(wireless_column_name)
                if wireless_number in existing_wireless_data:
                    # Existing row found, compare each field for changes
                    old_row = existing_wireless_data[wireless_number]
                    updated_fields = {}
                    for field in df_csv.columns:
                        new_value = new_row[field]
                        old_value = old_row.get(field)

                        # Check if the field's new value differs from old value, handle NaT if present
                        if pd.notna(new_value) and new_value != old_value:
                            updated_fields[field] = new_value

                    # If any updates are found, log both previous and updated fields
                    if updated_fields:
                        previous_data_log.append(self.clean_data_for_json(old_row))  # Full old row for reference
                        new_data_log.append(self.clean_data_for_json(updated_fields))  # Only changed fields for new data
                else:
                    # For new wireless numbers, log the entire row in new data
                    new_data_log.append(self.clean_data_for_json(new_row.to_dict()))
            print("*****88")
            return {
                'message': 'process done',
                'error':0
            }
    
        except Exception as e:
            print(e)
            return {'message' : str(e), 'error' : -1}
    def clean_data_for_json(self, data):
        cleaned_data = {}
        for key, value in data.items():
            if isinstance(value, pd.Timestamp):
                cleaned_data[key] = value.isoformat() if not pd.isna(value) else None
            elif pd.isna(value):
                cleaned_data[key] = None
            else:
                cleaned_data[key] = value
        return cleaned_data