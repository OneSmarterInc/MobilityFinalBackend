from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable, BaselineDataTable
from .ser import OrganizationShowSerializer, VendorShowSerializer, BaselineDataTableShowSerializer, showOnboardedSerializer
from Dashboard.ModelsByPage.DashAdmin import Vendors
from checkbill import prove_bill_ID
from ..viewbill.ser import BaselinedataSerializer
class UploadedBillView(APIView):
    
    permission_classes = [IsAuthenticated]

    def __init__(self):
        self.filtered_baseline = None

    def get(self, request, *args, **kwargs):
        orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
        vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None), many=True)

        
        if request.GET:
            org = request.GET.get('org')
            vendor = request.GET.get('ven')
            ban = request.GET.get('ban')
            invoice_number = request.GET.get('invoicenumber')
            billdate = request.GET.get('billdate')
            formatted_billdate = format_date(billdate) if billdate else None
            duedate = request.GET.get('duedate')
            formatted_duedate = format_date(duedate) if duedate else None
            base = BaseDataTable.objects.filter(banOnboarded=None,banUploaded=None).filter(sub_company=org, vendor=vendor, accountnumber=ban)
            if not base.exists():
                return Response({"message": f"No baseline found for account number {ban}"}, status=status.HTTP_404_NOT_FOUND)
            if invoice_number:
                print("invoice number", invoice_number)
                base = base.filter(invoicenumber=invoice_number)
                if not base.exists():
                    return Response({"message": f"No baseline found for invoice {invoice_number}"}, status=status.HTTP_404_NOT_FOUND)
            if formatted_billdate:
                print(formatted_billdate)
                month = formatted_billdate.split()[0]
                year = formatted_billdate.split()[2]
                base = base.filter(month=month,year=year)
                if not base.exists():
                    return Response({"message": f"No baseline found for bill date {billdate}"}, status=status.HTTP_404_NOT_FOUND)
            if formatted_billdate and formatted_duedate:
                month = formatted_duedate.split()[0]
                year = formatted_duedate.split()[2]
                base = base.filter(date_due=duedate)
                if not base.exists():
                    return Response({"message": f"No baseline found for bill date {duedate}"}, status=status.HTTP_404_NOT_FOUND)

            if len(base) == 1:
                baseline = BaselineDataTable.objects.filter(viewuploaded=base[0].viewuploaded,viewpapered=base[0].viewpapered).filter(is_draft=False, is_pending=False)
            else:
                return Response({"message":"Internal Server Error"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            wireless_numbers = baseline.values_list('Wireless_number', flat=True)
            Onboardedobjects = BaselineDataTable.objects.filter(
                viewuploaded=None,
                viewpapered=None,
                vendor=vendor,
                account_number=ban,
                sub_company=org,
                Wireless_number__in=wireless_numbers
            )
            self.filtered_baseline = BaselinedataSerializer(baseline, many=True, context={'onboarded_objects': Onboardedobjects}).data
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "onborded": onboarded.data, "filtered_baseline": self.filtered_baseline},
            status=status.HTTP_200_OK,
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
            main_onboarded = BaselineDataTable.objects.filter(viewuploaded=None,viewpapered=None, account_number=obj.account_number, sub_company=obj.sub_company, vendor=obj.vendor, Wireless_number=obj.Wireless_number)
            if main_onboarded.exists():
                main_onboarded = main_onboarded[0]
                main_onboarded.category_object = cat
                main_onboarded.save()
            unique_onboarded = UniquePdfDataTable.objects.filter(viewuploaded=None,viewpapered=None, account_number=obj.account_number, sub_company=obj.sub_company, vendor=obj.vendor, wireless_number=obj.Wireless_number)
            if unique_onboarded.exists():
                unique_onboarded = unique_onboarded[0]
                unique_onboarded.category_object = cat
                unique_onboarded.save()
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
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None), many=True)

        baseline = BaselineDataTable.objects.filter(banOnboarded=None,banUploaded=None)
        wireless_numbers = baseline.values_list('Wireless_number', flat=True)
        Onboardedobjects = BaselineDataTable.objects.filter(
            viewuploaded=None,
            viewpapered=None,
            Wireless_number__in=wireless_numbers
        )
        baselineData = BaselinedataSerializer(baseline, many=True, context={'onboarded_objects': Onboardedobjects})

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
            main_onboarded = BaselineDataTable.objects.filter(viewuploaded=None, account_number=obj.account_number, sub_company=obj.sub_company, vendor=obj.vendor, Wireless_number=obj.Wireless_number)
            if main_onboarded.exists():
                main_onboarded = main_onboarded[0]
                main_onboarded.category_object = cat
                main_onboarded.save()
            unique_onboarded = UniquePdfDataTable.objects.filter(viewuploaded=None, account_number=obj.account_number, sub_company=obj.sub_company, vendor=obj.vendor, wireless_number=obj.Wireless_number)
            if unique_onboarded.exists():
                unique_onboarded = unique_onboarded[0]
                unique_onboarded.category_object = cat
                unique_onboarded.save()
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
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None), many=True)
        baseline = BaselineDataTable.objects.filter(banOnboarded=None,banUploaded=None, is_draft=True)
        wireless_numbers = baseline.values_list('Wireless_number', flat=True)
        Onboardedobjects = BaselineDataTable.objects.filter(
            viewuploaded=None,
            Wireless_number__in=wireless_numbers
        )
        baselineData = BaselinedataSerializer(baseline, many=True, context={'onboarded_objects': Onboardedobjects})
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
            main_onboarded = BaselineDataTable.objects.filter(viewuploaded=None, account_number=obj.account_number, sub_company=obj.sub_company, vendor=obj.vendor, Wireless_number=obj.Wireless_number)
            if main_onboarded.exists():
                main_onboarded = main_onboarded[0]
                main_onboarded.category_object = cat
                main_onboarded.save()
            unique_onboarded = UniquePdfDataTable.objects.filter(viewuploaded=None, account_number=obj.account_number, sub_company=obj.sub_company, vendor=obj.vendor, wireless_number=obj.Wireless_number)
            if unique_onboarded.exists():
                unique_onboarded = unique_onboarded[0]
                unique_onboarded.category_object = cat
                unique_onboarded.save()
            
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

from ..models import ViewUploadBill, ProcessedWorkbook
from OnBoard.Ban.models import MappingObjectBan
import ast
import pdfplumber
from django.forms.models import model_to_dict

from checkbill import prove_bill_ID
from View.enterbill.ep import EnterBillProcessExcel

class UploadfileView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        self.processed_data = None
        self.paylod_data = None

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
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).exclude(Entry_type="Master Account"), many=True)

        baselineData = BaselineDataTableShowSerializer(BaselineDataTable.objects.all(), many=True)

        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "baseline":baselineData.data, "onborded":onboarded.data},
            status=status.HTTP_200_OK,
        )
    def post(self, request, *args, **kwargs):
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
        print("ban==",ban)
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

        found = BaseDataTable.objects.exclude(banUploaded=None, banOnboarded=None).filter(sub_company=org, vendor=vendor, accountnumber=ban)
        if not found.exists():
            return Response({"message":f"ban with account number {ban} not found!"},status=status.HTTP_400_BAD_REQUEST)
        if found.exists():
            print("Founded")
            if 'master' in found[0].Entry_type.lower():
                return Response({
                    "message": f"ban with Master Account is not acceptable!"
                }, status=status.HTTP_400_BAD_REQUEST)
        
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

        if 'mobile' in str(obj.vendor.name) and obj.file.name.endswith('.pdf'):
            check_type = self.check_tmobile_type(obj.file.path)
            if check_type == 1:
                obj.types = 'first'
                tp = 1
            elif check_type == 2:
                obj.types ='second'
                tp = 2
            else:
                obj.types = None
                tp = None
        else:
            tp = None
                
        if str(file.name).endswith('.pdf'):
            try:
                addon = InitialProcessPdf(instance=obj, user_mail=request.user.email,tp=tp)
                check = addon.startprocess()
                print(check)
                if check['error'] != 0:
                    obj.delete()
                    return Response(
                        {"message": f"Problem to upload file, {str(check['message'])}"}, status=status.HTTP_400_BAD_REQUEST
                    )
            except Ex:
                obj.delete()
            
            
            buffer_data = json.dumps({'pdf_path': obj.file.path,'vendor_name': obj.vendor.name if obj.vendor else None,'pdf_filename':obj.file.name,'company_name':obj.company.Company_name if obj.company else None,'sub_company_name':obj.organization.Organization_name if obj.organization else None,'types':obj.types, 'month':obj.month, 'year':obj.year, 'email':request.user.email,'account_number':obj.ban})
            print(buffer_data)
            verizon_att_enterBill_processor.delay(buffer_data, obj.id,btype=tp)
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
                obj.delete()
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
                'excel_csv_path': obj.file.path,
                'company': obj.company.Company_name if obj.company else None,
                'sub_company': obj.organization.Organization_name if obj.organization else None,
                'vendor': obj.vendor.name if obj.vendor else None,
                'account_number': obj.ban,
                'month':obj.month,
                'year':obj.year,
                'mapping_json': model_to_dict(MappingObjectBan.objects.get(viewupload=obj)) or {}
            })
            print(buffer_data)

            try:
                excelobj = EnterBillProcessExcel(buffer_data=buffer_data, instance=obj)
                msgobject = excelobj.process_excel()
                print(msgobject)
                if msgobject['code'] != 0:
                    obj.delete()
                    return Response({"message":f"{str(msgobject['message'])}"},status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print(e)
                obj.delete()
                return Response({"message":f"{str(e)}"},status=status.HTTP_400_BAD_REQUEST)
        elif str(file.name).endswith('.zip'):
            addon = ProcessZip(obj)
            check = addon.startprocess()
            print(check)
            if check['error'] == -1:
                return Response(
                    {"message": f"Problem to add data, {str(check['message'])}"}, status=status.HTTP_400_BAD_REQUEST
                )
            
        else:
            return Response({"message": "Invalid file type"}, status=status.HTTP_400_BAD_REQUEST)
        paylod_data = BaseDataTable.objects.filter(viewuploaded=obj).first()
        self.paylod_data = {
            'sub_company':paylod_data.sub_company,
            'vendor':paylod_data.vendor,
            'account_number':paylod_data.accountnumber,
            'bill_date':paylod_data.bill_date
        } if filetype in ("zip","excel") else None
        print(paylod_data)
        saveuserlog(
            request.user,
            f"Uploading file if {obj.vendor.name}-{obj.ban} for {obj.month}-{obj.year}"
        )
        return Response(
            {"message": "File uploaded successfully!" if filetype in ("zip","excel") else "The bill upload is currently in progress and may take some time. You will receive an email notification once the process is complete.", "payload":self.paylod_data},
            status=status.HTTP_200_OK,
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
            main_onboarded = BaselineDataTable.objects.filter(viewuploaded=None, account_number=obj.account_number, sub_company=obj.sub_company, vendor=obj.vendor, Wireless_number=obj.Wireless_number)
            if main_onboarded.exists():
                main_onboarded = main_onboarded[0]
                main_onboarded.category_object = cat
                main_onboarded.save()
            unique_onboarded = UniquePdfDataTable.objects.filter(viewuploaded=None, account_number=obj.account_number, sub_company=obj.sub_company, vendor=obj.vendor, wireless_number=obj.Wireless_number)
            if unique_onboarded.exists():
                unique_onboarded = unique_onboarded[0]
                unique_onboarded.category_object = cat
                unique_onboarded.save()
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
def parse_until_dict(data):
    while isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            break
    return data
from addon import get_close_match_key
def tagging(baseline_data, bill_data):
    baseline_data = parse_until_dict(baseline_data)
    bill_data = parse_until_dict(bill_data)
    def compare_and_tag(base, bill):
        for key in list(bill.keys()):
            if not key in base.keys():
                closely_matched = get_close_match_key(key,list(base.keys()))
            else:
                closely_matched = key
            if not closely_matched:
                print("not closely matched!",key)
                bill[key] = {"amount": f'{str(bill[key]).strip().replace("$","")}', "approved": False}
                continue
            base_val = base[closely_matched]
            bill_val = bill[key]

            if isinstance(bill_val, dict) and isinstance(base_val, dict):
                compare_and_tag(base_val, bill_val)
            else:
                try:
                    base_val = str(base_val).replace('$','').replace('-','')
                    bill_val_init = str(bill_val).replace('$','')
                    bill_val = bill_val_init.replace('-','')
                    base_float = float(base_val)
                    bill_float = float(bill_val)
                    if base_float == 0 and bill_float == 0:
                        bill[key] = {"amount": f'{bill_val}', "approved": True}
                    if base_float != 0:
                        low_range = bill_float - (5/100 * bill_float)
                        high_range = bill_float + (5/100 * bill_float)
                        if ((base_float < high_range) and (base_float > low_range)):
                            tag = True
                        else:
                            tag = False
                        if '-' in bill_val_init:
                            bill[key] = {"amount":f'-{bill_val}', "approved":tag}
                        else:
                            bill[key] = {"amount":bill_val, "approved":tag}
                except (ValueError, TypeError):
                    print("error")
                    bill[key] = {"amount":bill_val, "approved":False}

    compare_and_tag(baseline_data, bill_data)
    json_string = json.dumps(bill_data)
    return json_string



# from .tasks import process_view_bills
from View.enterbill.tasks import process_view_bills, process_view_excel, verizon_att_enterBill_processor
import re
import os
import zipfile
import pandas as pd
from checkbill import check_tmobile_type, checkVerizon, checkAtt, checkTmobile1, checkTmobile2
from io import StringIO, BytesIO
class InitialProcessPdf:
    def __init__(self, user_mail, instance,tp, **kwargs):
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
        self.type = tp
        self.file_acc = None
        self.file_bill_date = None
        self.file_billing_name = None
    def startprocess(self):
        matching_page_basic = []
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
        

        with pdfplumber.open(self.path) as pdf:
            pages = pdf.pages
            for i, page in enumerate(pages):
                text = page.extract_text()
                if "account" in text.lower() and re.findall(r"\b\d{5}-\d{4}\b", text):
                    if not matching_page_basic:
                        matching_page_basic.append(page)
                        if self.type == 1:
                            page1 = pages[i+1].within_bbox(((0, 0, page.width/2, 200)))
                            text = page1.extract_text()
                            pattern = re.compile(r"""
                                (                       
                                (?:[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}) 
                                )                       
                            """, re.VERBOSE)
                            matches = pattern.search(text)
                            self.file_bill_date = matches[0].replace(",","") if matches else None
                        break
        if not matching_page_basic:
            return {
                    'message': f'Unable to process pdf may be due to unsupported format',
                    'error': -1
                }

        if "verizon" in self.vendor.lower():
            self.file_acc, self.file_bill_date, self.file_billing_name = checkVerizon(matching_page_basic)
        elif "mobile" in self.vendor.lower():
            if self.type == 2:
                self.file_acc, self.file_bill_date, self.file_billing_name = checkTmobile2(matching_page_basic)
            elif self.type == 1:
                self.file_acc, self.file_billing_name = checkTmobile1(matching_page_basic)
            else:
                return {'message' : f'Unable to process file, might be due to unsupported file format.', 'error' : -1}
        else:
            self.file_acc, self.file_bill_date, self.file_billing_name = checkAtt(matching_page_basic)

        print(self.file_acc, self.org, self.company, self.file_bill_date, self.file_billing_name)
        
        if not self.file_acc and not self.file_bill_date:
            return {'message' : f'Unable to process file, might be due to unsupported file format.', 'error' : -1}
        # if "verizon" in str(self.vendor).lower():
        #     if not self.check_billing_name(self.org, self.file_billing_name):
        #         return {'message' : f'Organization name from the Pdf file did not matched with {self.org}', 'error' : -1}

        bill_date_pdf = self.file_bill_date.split(" ")
        if self.file_acc != self.account_number:
            return {'message' : f'Account number from the Pdf file did not matched with input ban', 'error' : -1}
        
        if not (bill_date_pdf[0].lower() in self.month.lower()):
            return {'message' : f'Bill date from the Pdf file did not matched with input month', 'error' : -1}

        if self.year != bill_date_pdf[2]:
            return {'message' : f'Bill date from the Pdf file did not matched with input year', 'error' : -1}
        if BaseDataTable.objects.filter(accountnumber=self.file_acc, sub_company=self.org, month=self.month, year=self.year):  # temprory set to not
            return {'message' : f'The bill with account number {self.file_acc} and bill date {self.file_bill_date} already exists', 'error' : -1}
        return {
            'message': 'Process Done',
            'error': 0,
        }
    
    def check_billing_name(self, org, billing_name):
        is_match = False
        if org.lower() != billing_name.lower():
            if org.lower() == "babw" and "build-a-bear" in billing_name.lower():
                is_match = True
            elif 'arch' in org.lower() and 'arch' in billing_name.lower():
                is_match = True
        print("is_match=", is_match)
        return is_match
    
from django.conf import settings
from django.core.files import File
import shutil
import io
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
        self.vendor = instance.vendor
        self.month = instance.month
        self.masteraccount = instance.ban
        self.year = instance.year
        self.types = None
        self.ban = instance.ban
        self.account_number = None
        self.net_amount = None
    def get_cust_data_from_db(self, acc_no,Eid):
        print("def get_cust_data_from_db")
        account_number = acc_no

        # Fetch data using Django ORM
        data = list(UniquePdfDataTable.objects.filter(viewuploaded=Eid).filter(account_number=account_number)
                    .values('wireless_number', 'user_name', 'cost_center', 'total_charges'))

        # Create DataFrame
        columns = ['wireless_number', 'user_name', 'cost_center', 'total_charges']
        df = pd.DataFrame(data, columns=columns)

        if df['cost_center'].isnull().all():
            df = df.drop('cost_center', axis=1)
            return df
        else:
            df['total_charges'] = df['total_charges'].replace('[\$,]', '', regex=True).astype(float)

            # Group by cost_center and sum total_charges
            grouped_df = df.groupby('cost_center')['total_charges'].sum().reset_index()
            grouped_df.columns = ['cost_center', 'sum_of_total_current_charges']

            # Merge grouped data with original DataFrame
            result_df = pd.merge(df, grouped_df, on='cost_center', how='left')
            result_df['Row_labels'] = result_df['cost_center']
            result_df = result_df[['wireless_number', 'user_name', 'cost_center', 'total_charges', 'Row_labels', 'sum_of_total_current_charges']]

            return result_df
    def generate_excel(self, s1,s2,s3,s4):
        s1.rename(columns={'sub_company':'Sub Company',},inplace=True)
        s2.rename(columns={'sub_company':'Sub Company',},inplace=True)
        s3.rename(columns={'sub_company':'Sub Company',},inplace=True)
        s4.rename(columns={'sub_company':'Sub Company',},inplace=True)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            s1.to_excel(writer, sheet_name='Sheet1', index=False)
            s2.to_excel(writer, sheet_name='Sheet2', index=False)
            s3.to_excel(writer, sheet_name='Sheet3', index=False)
            s4.to_excel(writer, sheet_name='Sheet4', index=False)
        output.seek(0)
        return output
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
            if 'mobile' in str(self.vendor).lower() and self.path.endswith('.pdf'):
                self.types = check_tmobile_type(self.path)

            if self.path.endswith('.zip'):
                
                data_base, data_pdf,detailed_df,required_df = self.extract_rdd_data(self.path,self.org)
                print(data_pdf)
                print(detailed_df)
                print(required_df)
                pattern = r'\d{3}[-.]\d{3}[-.]\d{4}'
                data_pdf = data_pdf[data_pdf['wireless_number'].astype(str).str.match(pattern, na=False)]


                detailed_df = detailed_df[detailed_df['Wireless Number'].astype(str).str.match(pattern, na=False)]
                data_base['company'] = self.company
                data_base['vendor'] = self.vendor
                data_base['sub_company'] = self.org
                data_base['master_account'] = self.masteraccount
                data_base['Total_Current_Charges'] = list(required_df['Total Current Charges'])[0]
                data_base['RemittanceAdd'] = list(required_df['Remittance Address'])[0]
                data_base['BillingName'] = list(required_df['Bill Name'])[0]
                self.net_amount = list(required_df['Total Amount Due'])[0]
                data_base['Total_Amount_Due'] = list(required_df['Total Amount Due'])[0]

                v, t = None, None
                category_data = data_pdf.to_dict(orient='records')
                for entry in category_data:
                    entry['company'] = self.company
                    entry['vendor'] = self.vendor
                

                for entry in data_pdf.to_dict(orient="records"):
                    entry['company'] = self.company
                    entry['vendor'] = self.vendor
                acc_no = data_base['accountnumber']
                bill_date = data_base.pop('bill_date').replace(",","").split(" ")
                data_base['bill_date'] = " ".join(bill_date)
                if acc_no != self.ban:
                    self.instance.delete()
                    return {'message' : f'Account number from the RDD file did not matched with input ban', 'error' : -1}
                if not (bill_date[0] in str(self.month)):
                    self.instance.delete()
                    return {'message' : f'Bill date from the RDD file did not matched with input month', 'error' : -1}
                if self.year != bill_date[2]:
                    self.instance.delete()
                    return {'message' : f'Bill date from the RDD file did not matched with input year', 'error' : -1}
                if BaseDataTable.objects.filter(accountnumber=acc_no, company=self.company, sub_company=self.org, month=self.month, year=self.year).exists():
                    self.instance.delete()
                    return {'message' : f'Bill already exists for account number {acc_no}', 'error' : -1}
                else:
                    obj = BaseDataTable.objects.create(viewuploaded=self.instance,month=self.month, year=self.year,net_amount=self.net_amount, **data_base)
                    print("saved to base data table")
                    self.account_number = obj.accountnumber
                    obj.save()
                bill_main_id = obj.viewuploaded.id
                onboarded_id = BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).filter(sub_company=obj.sub_company, vendor=obj.vendor, accountnumber=obj.accountnumber).first().banOnboarded
                print('done')
                self.save_to_pdf_data_table(data_pdf, v, t,obj)
                print("saved to pdf data table")
                # self.save_to_batch_report(data_base, self.vendor)
                # print('saved to batch report')
                self.save_to_unique_pdf_data_table(data_pdf, v, t,obj)

                print('saved to unique pdf data table')
                from collections import defaultdict
                wireless_data = defaultdict(lambda: defaultdict(dict))
                tmp_df = detailed_df
                tmp_df.rename(columns={'Item Category':'Item_Category','Item Description':'Item_Description','Wireless Number':'Wireless_number'},inplace=True)
                for idx, row in tmp_df.iterrows():
                    wireless_number = row['Wireless_number']
                    item_category = str(row['Item_Category']).strip().upper() if 'Item_Category' in row else None
                    item_description = str(row['Item_Description']).strip().upper() if 'Item_Description' in row else None
                    charges = str(row['Charges']).replace("$",'')
                    if pd.notna(item_category) and pd.notna(item_description) and pd.notna(charges):
                        wireless_data[wireless_number][item_category][item_description] = charges
                    
                result_list = [dict(wireless_data)]
                udf = pd.DataFrame(data_pdf)
                wireless_numbers = []
                charges_objects = []
                for entry in result_list:
                    for number, charges in entry.items():
                        wireless_numbers.append(number)
                        charges_objects.append(charges) 
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
                self.save_to_baseline_data_table(category_data, self.vendor,date=" ".join(bill_date) if isinstance(bill_date,list) else bill_date, types=self.types,baseobj=obj)
                print("saved to baseline data table")
                cusdf = self.get_cust_data_from_db(self.account_number, bill_main_id)
                workbook = self.generate_excel(s1=required_df,s2=data_pdf,s3=detailed_df,s4=cusdf)
                workbook_name = str(self.path).split("/")[-1].replace(".zip", ".xlsx")

                output_dir = os.path.join(settings.MEDIA_ROOT, "ViewUploadedBills")
                os.makedirs(output_dir, exist_ok=True)
                output_file_path = os.path.join(output_dir, workbook_name)
                try:
                    with open(output_file_path, "wb") as f:
                        f.write(workbook.getvalue())

                    # Create ProcessedWorkbook instance (WITHOUT setting the FileField yet)
                    processed_workbook = ProcessedWorkbook(
                        uploadbill=self.instance,
                        account_number=self.account_number,
                        vendor_name=self.vendor,
                        company_name=self.company,
                        sub_company_name=self.org,
                        workbook_name=workbook_name,
                        bill_date_info=obj.bill_date
                    )
                    
                    # Open the saved file and keep it open for Django
                    f = open(output_file_path, "rb")  # DO NOT USE `with open(...)`
                    django_file = File(f, name=workbook_name)

                    processed_workbook.output_file = django_file
                    self.instance.output_file = django_file
                    
                    processed_workbook.save()
                    self.instance.save()
                    obj.workbook_path = processed_workbook.output_file.url
                    obj.save()

                    f.close()

                except Exception as e:
                    print(e)
                self.reflect_uniquetable_non_bill_data(bill_main_id=bill_main_id, onboarded_id=onboarded_id)
                self.reflect_baselinetable_non_bill_data(bill_main_id=bill_main_id, onboarded_id=onboarded_id)
                self.add_tag_to_dict(bill_main_id)
                self.reflect_category_object(bill_main_id)
                self.check_baseline_approved(UniquePdfDataTable, bill_main_id)
                self.check_baseline_approved(BaselineDataTable, bill_main_id)
                
                
                account_obj = BaselineDataTable.objects.filter(viewuploaded=self.instance).filter(sub_company=self.org, vendor=self.vendor, account_number=self.account_number)
                approved_wireless_list = account_obj.values_list('is_baseline_approved', flat=True)
                obj.is_baseline_approved = False if False in list(approved_wireless_list) else True
                obj.save()                
                return {'message' : 'RDD uploaded successfully!', 'error' : 1}
        except Exception as e:
            print(f'Error occurred while processing zip file: {str(e)}')
            self.instance.delete()
            return {'message' : f'Error occurred while processing zip file: {str(e)}', 'error' : -1}
    
            
    def save_to_baseline_data_table(self, data, vendor,date, types, baseobj):
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
        data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage","Bill_Cycle_Date":"bill_date"},inplace=True)

        data_df = data_df.drop(columns=['company', 'vendor'], errors='ignore') 

        if 'category_object' in data_df.columns:
            data_df['category_object'] = data_df['category_object'].apply(
                lambda x: json.dumps(x)
            )

        data = data_df.to_dict(orient='records')

        objects_to_create = [
            BaselineDataTable(
                viewuploaded=self.instance,
                **item,
                company=self.company,
                vendor=self.vendor,
                bill_date=date
            )
            for item in data
        ]


        BaselineDataTable.objects.bulk_create(objects_to_create, ignore_conflicts=True)
        
        get_main_base_obj = BaseDataTable.objects.filter(viewuploaded=None, sub_company=baseobj.sub_company, vendor=baseobj.vendor, accountnumber=baseobj.accountnumber)
        get_main_base_obj = get_main_base_obj[0] if get_main_base_obj.exists() else None
        for obj in objects_to_create:
            existing = BaselineDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(
                sub_company=obj.sub_company,
                vendor=obj.vendor,
                account_number=obj.account_number,
                Wireless_number=obj.Wireless_number,
            )
            if not existing.exists():
                print("not exists")
                
                # print("new object data", model_to_dict(obj))
                # print("get main base obj", model_to_dict(get_main_base_obj))
                new_obj_data = model_to_dict(obj)
                new_obj_data['viewuploaded'] = None
                if get_main_base_obj.banUploaded:
                    new_obj_data['banUploaded'] = get_main_base_obj.banUploaded
                elif get_main_base_obj.banOnboarded:
                    new_obj_data['banOnboarded'] = get_main_base_obj.banOnboarded
                elif get_main_base_obj.inventory:
                    new_obj_data['inventory'] = get_main_base_obj.inventory
                new_obj = BaselineDataTable.objects.create(**new_obj_data)
                
                new_obj.save()



    def save_to_unique_pdf_data_table(self, data, vendor,types,baseobj):
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
            UniquePdfDataTable(viewuploaded=self.instance, vendor=self.vendor, company=self.company, **{key: value for key, value in item.items() if key in model_fields})
            for item in data
        ]
        # Bulk insert records
        print("number of lines in enter bill=", len(objects_to_create))
        UniquePdfDataTable.objects.bulk_create(objects_to_create, ignore_conflicts=True)
        
        get_main_base_obj = BaseDataTable.objects.filter(viewuploaded=None, sub_company=baseobj.sub_company, vendor=baseobj.vendor, accountnumber=baseobj.accountnumber)
        get_main_base_obj = get_main_base_obj[0] if get_main_base_obj.exists() else None
        for obj in objects_to_create:
            existing = UniquePdfDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(
                sub_company=obj.sub_company,
                vendor=self.vendor,
                account_number=obj.account_number,
                wireless_number=obj.wireless_number,
            )
            if not existing.exists():
                print("not exists")

                new_obj_data = model_to_dict(obj)
                new_obj_data['viewuploaded'] = None
                if get_main_base_obj.banUploaded:
                    new_obj_data['banUploaded'] = get_main_base_obj.banUploaded
                elif get_main_base_obj.banOnboarded:
                    new_obj_data['banOnboarded'] = get_main_base_obj.banOnboarded
                elif get_main_base_obj.inventory:
                    new_obj_data['inventory'] = get_main_base_obj.inventory
                new_obj = UniquePdfDataTable.objects.create(**new_obj_data)
                
                new_obj.save()

    def reflect_uniquetable_non_bill_data(self,onboarded_id,bill_main_id):
        current_bill = UniquePdfDataTable.objects.filter(
            company=self.company,
            sub_company=self.org,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        uploaded_baseline = UniquePdfDataTable.objects.filter(
            company=self.company,
            sub_company=self.org,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=None,
            viewpapered=None
        )
        current_numbers = current_bill.values_list('wireless_number', flat=True)
        uploaded_numbers = uploaded_baseline.values_list('wireless_number', flat=True)
        missing_numbers = set(current_numbers) - set(uploaded_numbers)
        print("length of missing uniques", len(missing_numbers))
        missing_entries = current_bill.filter(wireless_number__in=missing_numbers)
        new_entries = []
        for entry in missing_entries:
            entry.pk = None  # This ensures a new row is created on save
            entry.viewuploaded = None
            entry.viewpapered = None
            entry.banOnboarded = onboarded_id
            new_entries.append(entry)
        
        UniquePdfDataTable.objects.bulk_create(new_entries)
    def reflect_baselinetable_non_bill_data(self,onboarded_id,bill_main_id):
        current_bill = BaselineDataTable.objects.filter(
            company=self.company,
            sub_company=self.org,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        uploaded_baseline = BaselineDataTable.objects.filter(
            company=self.company,
            sub_company=self.org,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=None,
            viewpapered=None
        )
        current_numbers = current_bill.values_list('Wireless_number', flat=True)
        uploaded_numbers = uploaded_baseline.values_list('Wireless_number', flat=True)
        missing_numbers = set(current_numbers) - set(uploaded_numbers)
        print("length of missing baselines", len(missing_numbers))
        missing_entries = current_bill.filter(Wireless_number__in=missing_numbers)
        new_entries = []
        for entry in missing_entries:
            entry.pk = None  # This ensures a new row is created on save
            entry.viewuploaded = None
            entry.viewpapered = None
            entry.banOnboarded = onboarded_id
            new_entries.append(entry)
        
        BaselineDataTable.objects.bulk_create(new_entries)
    
    def add_tag_to_dict(self, bill_main_id):
        print("def add_tag_to_dict")
        baseline = BaselineDataTable.objects.filter(
            company=self.company,
            sub_company=self.org,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=None,
            viewpapered=None
        )
        current_bill = BaselineDataTable.objects.filter(
            company=self.company,
            sub_company=self.org,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
    
        baseline_dict = {b.Wireless_number: b for b in baseline if b.Wireless_number}
        for bill_obj in current_bill:
            wireless = bill_obj.Wireless_number
            baseline_obj = baseline_dict.get(wireless)
            if baseline_obj:  
                tagged_object = tagging(baseline_obj.category_object, bill_obj.category_object)
                bill_obj.category_object = tagged_object
                bill_obj.save()

    def check_baseline_approved(self, model,bill_main_id):
        all_objects = model.objects.filter(
            company=self.company,
            sub_company=self.org,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        for line in all_objects:
            line.is_baseline_approved = check_true_false(line.category_object)
            line.save()

    def reflect_category_object(self, bill_main_id):
        uniques = UniquePdfDataTable.objects.filter(
            company=self.company,
            sub_company=self.org,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )

        for line in uniques:
            baseline = BaselineDataTable.objects.filter(
                company=line.company,
                sub_company=line.sub_company,
                vendor=line.vendor,
                account_number=self.account_number,
                viewuploaded=bill_main_id,
                Wireless_number=line.wireless_number,
            ).first()

            if baseline:
                line.category_object = baseline.category_object
                line.save()
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
            "Bill_Cycle_Date":"bill_date"
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
            'Total_Current_Charges': 'Net_Amount',
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
            'foundation_account',
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
            BatchReport.objects.create(viewuploaded=self.instance, **renamed_data)

            if 'new_location_code' in locals() and new_location_code:
                BatchReport.objects.filter(
                    Vendor_Zip=entered_vendor_zip, Vendor_State=entered_vendor_state, Vendor_City=entered_vendor_city
                ).update(Location_Code=new_location_code)

    def save_to_pdf_data_table(self, data, vendor, types,baseobj):
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
        for item in data:
            bill_date = item.pop('bill_date').replace(",","")
            BaseDataTable.objects.create(viewuploaded=self.instance,bill_date=bill_date, **item)


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
        shutil.rmtree(directory, ignore_errors=True)
    
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
    
class ApproveView(APIView):
    permission_classes = [IsAuthenticated]

    
    def post(self, request,id, *args, **kwargs):
        data = request.data.copy()
        sub_company = data.pop('sub_company')
        vendor = data.pop('vendor')
        ban = data.pop('ban')
        wn = data.pop('wireless_number')

        if not (id and sub_company and ban and wn):
            return Response({"message":"Incomplete paylod"}, status=status.HTTP_400_BAD_REQUEST)
        
        main_object = data.pop('main_object')

        main_uploaded_id = BaselineDataTable.objects.filter(id=id).first()
        if not main_uploaded_id:
            return Response({"message":"object not found!"},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            enter_bill_baseline_objs = BaselineDataTable.objects.filter(viewuploaded=main_uploaded_id.viewuploaded,viewpapered=main_uploaded_id.viewpapered)

            onboard_baseline_objs = BaselineDataTable.objects.filter(viewuploaded=None,viewpapered=None, vendor=vendor, account_number=ban)

            if not onboard_baseline_objs.exists():
                return Response({"message":"Baseline data for given attributes Not found!"}, status=status.HTTP_400_BAD_REQUEST)

            enter_bill_unique_objs = UniquePdfDataTable.objects.filter(viewuploaded=main_uploaded_id.viewuploaded,viewpapered=main_uploaded_id.viewpapered)
            
            onboard_unique_objs = UniquePdfDataTable.objects.filter(viewuploaded=None,viewpapered=None, vendor=vendor, account_number=ban)
            if not enter_bill_unique_objs.exists():
                return Response({"message":"Unique data for given attributes Not found!"}, status=status.HTTP_400_BAD_REQUEST)
                
            # update baseline
            baseline = main_object['baseline']
            new_baseline = json.dumps(baseline)
            print(new_baseline)
            _obj = onboard_baseline_objs.filter(Wireless_number=wn).first()
            print(_obj.id)
            if _obj:
                _obj.category_object = new_baseline
                _obj.save()  

            u_obj = onboard_unique_objs.filter(wireless_number=wn).first()
            print(u_obj.id)
            if u_obj:
                u_obj.category_object = new_baseline
                u_obj.save() 


            # approve bill
            approve = main_object['approve']
            new_approved = json.dumps(approve)

            _obj = enter_bill_baseline_objs.filter(Wireless_number=wn).first()
            if _obj:
                _obj.category_object = new_approved
                _obj.is_baseline_approved = check_true_false(_obj.category_object)
                _obj.save()   

            u_obj = enter_bill_unique_objs.filter(wireless_number=wn).first()
            if u_obj:
                u_obj.category_object = new_approved
                u_obj.is_baseline_approved = check_true_false(u_obj.category_object)
                u_obj.save()  
            
            # approve whole
            approved_wireless_list = enter_bill_baseline_objs.values_list('is_baseline_approved', flat=True)

            base_obj = BaseDataTable.objects.filter(viewuploaded=_obj.viewuploaded,viewpapered= _obj.viewpapered)
            if base_obj.exists():
                base_instance = base_obj.first()
                base_instance.is_baseline_approved = False if False in approved_wireless_list else True
                base_instance.save()
            
            filtered_baseline = BaselinedataSerializer(enter_bill_baseline_objs, many=True, context={'onboarded_objects': onboard_baseline_objs})
            return Response({"message": "Baseline updated successfully!", "baseline":filtered_baseline.data}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ApproveFullView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        sub_cmpny = request.GET.get('org')
        ban = request.GET.get('ban')
        bill_date = request.GET.get('bill_date')
        main = BaseDataTable.objects.filter(sub_company=sub_cmpny, accountnumber=ban, bill_date=bill_date).first()
        if not main:
            return Response({"message":"Bill not found!"},status=status.HTTP_400_BAD_REQUEST)
        baselines = BaselineDataTable.objects.filter(viewpapered=main.viewpapered, viewuploaded=main.viewuploaded)
        uniquelines = UniquePdfDataTable.objects.filter(viewpapered=main.viewpapered, viewuploaded=main.viewuploaded)
        self.process_approval(baselines)
        self.process_approval(uniquelines)
        approved_wireless_list = baselines.values_list('is_baseline_approved', flat=True)
        main.is_baseline_approved = False if False in approved_wireless_list else True
        main.save()
        onboard_baseline_objs = BaselineDataTable.objects.filter(viewuploaded=None,viewpapered=None, sub_company=sub_cmpny, vendor=main.vendor, account_number=main.accountnumber)
        filtered_baseline = BaselinedataSerializer(baselines, many=True, context={'onboarded_objects': onboard_baseline_objs})
        return Response({"message":"Bill Approved Successfully", "baseline":filtered_baseline.data},status=status.HTTP_200_OK)
        
    def process_approval(self,queryset):
        updated_objects = []
        for obj in queryset:
            approve_obj = make_true_all(obj.category_object)
            obj.category_object = approve_obj
            obj.is_baseline_approved = check_true_false(approve_obj)
            updated_objects.append(obj)
        type(obj).objects.bulk_update(updated_objects, ['category_object', 'is_baseline_approved'])

    

class AprroveAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request,id, *args, **kwargs):
        main_uploaded_id = BaselineDataTable.objects.filter(id=id).first()
        print("man uploded id==", main_uploaded_id)
        if not main_uploaded_id:
            return Response({"message":"object not found!"},status=status.HTTP_400_BAD_REQUEST)
        try:
            approve_obj = make_true_all(main_uploaded_id.category_object)
            print("approve_obj==",approve_obj)
            main_uploaded_id.category_object = approve_obj
            main_uploaded_id.is_baseline_approved = check_true_false(main_uploaded_id.category_object)
            main_uploaded_id.save()
            

            enter_bill_unique_obj = UniquePdfDataTable.objects.filter(viewuploaded=main_uploaded_id.viewuploaded,viewpapered=main_uploaded_id.viewpapered, wireless_number=main_uploaded_id.Wireless_number).first()
            enter_bill_unique_obj.category_object = approve_obj
            enter_bill_unique_obj.is_baseline_approved = check_true_false(enter_bill_unique_obj.category_object)
            enter_bill_unique_obj.save()
            print(enter_bill_unique_obj)

            enter_bill_baseline_objs = BaselineDataTable.objects.filter(viewuploaded=main_uploaded_id.viewuploaded,viewpapered=main_uploaded_id.viewpapered)

            approved_wireless_list = enter_bill_baseline_objs.values_list('is_baseline_approved', flat=True)
            base_obj = BaseDataTable.objects.filter(viewuploaded=main_uploaded_id.viewuploaded,viewpapered= main_uploaded_id.viewpapered)
            if base_obj.exists():
                base_instance = base_obj.first()
                base_instance.is_baseline_approved = False if False in approved_wireless_list else True
                base_instance.save()
            onboard_baseline_objs = BaselineDataTable.objects.filter(viewuploaded=None,viewpapered=None, vendor=main_uploaded_id.vendor, account_number=main_uploaded_id.account_number)
            filtered_baseline = BaselinedataSerializer(enter_bill_baseline_objs, many=True, context={'onboarded_objects': onboard_baseline_objs})
            return Response({"message": "Baseline updated successfully!", "baseline":filtered_baseline.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AddNoteView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request,*args, **kwargs):
        data = request.data.copy()
        sub_company = data.pop('sub_company')
        vendor = data.pop('vendor')
        ban = data.pop('ban')
        bill_date = data.pop('bill_date')
        notes = data.pop('notes')
        base_obj = BaseDataTable.objects.filter(banUploaded=None, banOnboarded=None).filter(sub_company=sub_company, vendor=vendor, accountnumber=ban, bill_date=bill_date).first()
        if not base_obj:
            return Response({"message":"Bill not found!"},status=status.HTTP_400_BAD_REQUEST)
        base_obj.baseline_notes = str(notes).strip()
        base_obj.save()
        return Response({"message":"Notes added successfully!"},status=status.HTTP_200_OK)
    
def check_true_false(cat):
    formatted = json.loads(cat) if isinstance(cat, str) else cat
    for key, value in formatted.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, dict):
                    if sub_value['approved'] == False:
                        return False
    return True

def make_true_all(cat):
    formatted = json.loads(cat) if isinstance(cat, str) else cat
    for key, value in formatted.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, dict):
                    sub_value['approved'] = True
    return json.dumps(formatted)

from datetime import datetime
from ..models import PaperBill
class PaperBillView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filtered_baseline = None
    def get(self, request, *args, **kwargs):
        orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
        vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None), many=True)
        
        if request.GET:
            org = request.GET.get('org')
            vendor = request.GET.get('ven')
            ban = request.GET.get('ban')
            invoice_number = request.GET.get('invoicenumber')
            billdate = request.GET.get('billdate')
            duedate = request.GET.get('duedate')
            formatted_billdate = format_date(billdate)
            month = formatted_billdate.split(" ")[0]
            year = formatted_billdate.split(" ")[2]
            formatted_duedate = format_date(duedate)
            print(org, vendor, ban, invoice_number,month, year)
            
            base = BaseDataTable.objects.filter(sub_company=org, vendor=vendor, accountnumber=ban)
            if not base:
                return Response({"message":"Unexpected error occur!"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            print("base===")
            if base.filter(invoicenumber=invoice_number).exists():
                return Response({"message":f"Bill with invoice number {invoice_number} already exists!"},status=status.HTTP_400_BAD_REQUEST)
        

            if base.filter(month=month, year=year).exists():
                return Response({"message":f"Bill with month {month} and year {year} already exists!"},status=status.HTTP_400_BAD_REQUEST)

            new_paper_obj = PaperBill.objects.create(
                sub_company=org,
                vendor=vendor,
                account_number=ban,
                invoice_number=invoice_number,
                bill_date=formatted_billdate,
                due_date=formatted_duedate
            )
            new_paper_obj.save()
            print(base)
            new_base_obj = BaseDataTable.objects.create(
                viewpapered=new_paper_obj,
                company=base.first().company,
                sub_company=org,
                vendor=vendor,
                accountnumber=ban,
                invoicenumber=invoice_number,
                bill_date=formatted_billdate,
                date_due=formatted_duedate,
                month=formatted_billdate.split(" ")[0],
                year=formatted_billdate.split(" ")[2]
            )
            new_base_obj.save()
            
            onboarded_uniques = UniquePdfDataTable.objects.filter(viewuploaded=None,viewpapered=None).filter(sub_company=org, vendor=vendor, account_number=ban)
            onboarded_baseline = BaselineDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(sub_company=org, vendor=vendor, account_number=ban)

            print(len(onboarded_baseline), len(onboarded_uniques))

            new_uniques = []
            for unique in onboarded_uniques:
                unique.pk = None
                unique.banOnboarded = None
                unique.banUploaded = None
                unique.viewpapered = new_paper_obj
                unique.bill_date = formatted_billdate
                unique.category_object = {}
                new_uniques.append(unique)
            UniquePdfDataTable.objects.bulk_create(new_uniques)
            new_baselinies = []
            for line in onboarded_baseline:
                line.pk = None
                line.banOnboarded = None
                line.banUploaded = None
                line.viewpapered = new_paper_obj
                line.bill_date = formatted_billdate
                line.category_object = {}
                new_baselinies.append(line)
            BaselineDataTable.objects.bulk_create(new_baselinies)


            if new_base_obj:
                baseline = BaselineDataTable.objects.filter(viewpapered=new_base_obj.viewpapered).filter(is_draft=False, is_pending=False)
            else:
                return Response({"message":"Internal Server Error"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            wireless_numbers = baseline.values_list('Wireless_number', flat=True)
            Onboardedobjects = BaselineDataTable.objects.filter(
                viewpapered=None,
                viewuploaded=None,
                vendor=vendor,
                account_number=ban,
                sub_company=org,
                Wireless_number__in=wireless_numbers
            )
            self.filtered_baseline = BaselinedataSerializer(baseline, many=True, context={'onboarded_objects': Onboardedobjects}).data
        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "onborded": onboarded.data, "filtered_baseline": self.filtered_baseline},
            status=status.HTTP_200_OK,
        )

def format_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    formatted_date = date_obj.strftime("%B %d %Y")
    return formatted_date

    