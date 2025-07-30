from django.shortcuts import render, HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework import permissions
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company
from OnBoard.Ban.models import BatchReport, OnboardBan, BaseDataTable
from .ser import BatchReportSerializer, OrganizationShowSerializer, BaseDataSerializer
from openpyxl import Workbook
from sendmail import send_custom_email
# call update_or_create a django method
import ast
from io import BytesIO
from openpyxl.utils.dataframe import dataframe_to_rows

from django.core.files.base import ContentFile

from uuid import uuid4
from django.conf import settings
import os
import shutil
import pandas as pd
from django.forms import model_to_dict
# Create your views here.
class BatchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,org, *args, **kwargs):
        objs = BaseDataTable.objects.filter(sub_company=org).exclude(viewuploaded=None, viewpapered=None).filter(is_baseline_approved=True)
        serializer = BaseDataSerializer(objs, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
    
    def generate_excel_file(self, df):
        wb = Workbook()
        ws = wb.active

        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                        pass
                adjusted_width = max_length + 2
                ws.column_dimensions[column].width = adjusted_width
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        return excel_buffer 
    def post(self, request, *args, **kwargs):
        data = request.data
        if 'action' in data:
            org = data['sub_company']
            from_date = data['from_date']
            to_date = data['to_date']
            ids = ast.literal_eval(data['ids'])
            if type(ids) == int:
                base_ids = BaseDataTable.objects.filter(id=ids)
            else:
                base_ids = BaseDataTable.objects.filter(id__in=ids)

            df = pd.DataFrame.from_records(base_ids.values())
            df = df.drop(columns=['created', 'updated','auto_pay_enabled','Entry_type','master_account', 'website', 'Total_Current_Charges','plans','charges', 'location','duration','id', 'banUploaded_id','Total_Amount_Due', 'banOnboarded_id', 'viewuploaded_id','viewpapered_id', 'inventory_id','costcenterlevel', 'costcentertype','costcenterstatus', 'CostCenter', 'CostCenterNotes', 'PO','Displaynotesonbillprocessing', 'POamt', 'FoundAcc', 'bantype','invoicemethod', 'vendorCS', 'vendor_alias', 'month', 'year',
            'pdf_filename', 'pdf_path', 'remarks', 'account_password','payor', 'GlCode', 'ContractTerms', 'ContractNumber', 'Services','Billing_cycle', 'BillingDay', 'PayTerm', 'AccCharge','CustomerOfRecord', 'contract_name', 'contract_file', 'paymentType',
            'billstatus', 'banstatus', 'Check', 'summary_file','is_baseline_approved','workbook_path','batch_file','current_annual_review',
            'previous_annual_review'])

            batch = base_ids

            print(df.columns)
            
            if not batch:
                return Response({"message": f"No data found!"}, status=status.HTTP_404_NOT_FOUND)

            # Set the custom headings
            df.rename(columns={
                'bill_date': 'Bill Date',
                'date_due': 'Due Date',
                'accountnumber': 'Account Number',
                'invoicenumber': 'Invoice Number',
                'total_charges': 'Total Charges',
                'company': 'Company',
                'vendor': 'Vendor',
                'sub_company': 'Sub Company',
                'RemittanceAdd': 'Remittance Address',
                'BillingName': 'Billing Name',
                'BillingAdd': 'Billing Address',
                'BillingState': 'Billing State',
                'BillingZip': 'Billing Zip',
                'BillingCity': 'Billing City',
                'BillingCountry': 'Billing Country',
                'BillingAtn': 'Billing Attention',
                'BillingDate': 'Billing Date',
                'RemittanceName': 'Remittance Name',
                'RemittanceState': 'Remittance State',
                'RemittanceZip': 'Remittance Zip',
                'RemittanceCity': 'Remittance City',
                'RemittanceCountry': 'Remittance Country',
                'RemittanceAtn': 'Remittance Attention',
                'RemittanceNotes': 'Remittance Notes',
                'vendor_id': 'Vendor ID',
                'batch_approved': 'Batch Approved',
                'batch_approved_changer': 'Batch Approved By',
                'baseline_notes': 'Baseline Notes',
                'net_amount': 'Net Amount'
            }, inplace=True)

            
            # empty all 
            folder_path = os.path.join(settings.MEDIA_ROOT, "batchfiles")
            print(folder_path)
            shutil.rmtree(folder_path) if os.path.exists(folder_path) else None
            print(df[['Bill Date','Billing Name']])
            excel_buffer = self.generate_excel_file(df)
            obj = batch[0]
            if type(ids) == list:
                from_to = str(ids[0]) + '->' + str(ids[-1]) 
                BatchReport.objects.first()
            else:
                from_to = str(ids)
            file_name = f"batch_report_{from_to} .xlsx"
            obj.batch_file.save(file_name, ContentFile(excel_buffer.getvalue()), save=True)

            
            if data["action"] == "download":
                return Response({"data": obj.batch_file.url}, status=status.HTTP_200_OK)
            elif data['action'] == "send_mail":
                rm = data.get('to_mail')
                print("sending mail...")
                try:
                    send_custom_email(
                        receiver_mail=rm,
                        subject='Batch Report',
                        body='Please find the attached report.',
                        attachment=obj.batch_file
                    )
                    return Response({"message":f"Email sent successfully sent to {rm}"}, status=status.HTTP_200_OK)
                except Exception as e:
                    print(e)
                    return Response({"message":f"Error in sending mail:{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"message":"Invalid action!"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request,org, id, *args, **kwargs):
        try:
            obj = BaseDataTable.objects.get(id=id)
            data = request.data
            if 'type' in data:
                if data['type'] == 'status-change':
                    obj.batch_approved = data['status']
                    obj.batch_approved_changer = request.user.designation.name        
                obj.save()
                saveuserlog(request.user, f'Changed approves of Batch Report with ID: {id} to {data["status"]}')
            else:
                serializer = BaseDataSerializer(obj, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    saveuserlog(request.user, f'Updated Batch Report with ID: {id}')
                    return Response({'message': 'Batch Report updated successfully'}, status=status.HTTP_200_OK)
                else:
                    print(serializer.errors)
                    return Response({"message" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'message': 'Batch Report updated successfully'}, status=status.HTTP_200_OK)
        except BatchReport.DoesNotExist:
            return Response({'message': 'Batch Report not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f'Error in Batch Report update: {e}')
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request,org, id, *args, **kwargs):
        try:
            obj = BatchReport.objects.get(id=id)
            obj.delete()
            saveuserlog(request.user, f'Deleted Batch Report with ID: {id}')
            return Response({'message': 'Batch Report deleted successfully'}, status=status.HTTP_200_OK)
        except BatchReport.DoesNotExist:
            return Response({'message': 'Batch Report not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f'Error in Batch Report delete: {e}')
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
