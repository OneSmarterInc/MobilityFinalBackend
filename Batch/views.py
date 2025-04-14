from django.shortcuts import render, HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework import permissions
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company
from OnBoard.Ban.models import BatchReport, OnboardBan
from .ser import BatchReportSerializer, OrganizationShowSerializer
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
# Create your views here.
class BatchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        if request.user.designation.name == 'Admin':
            orgs = Organizations.objects.filter(company=request.user.company)
            objs = BatchReport.objects.filter(company=request.user.company.Company_name)
        else:
            orgs = Organizations.objects.all()
            objs = BatchReport.objects.all()
        serializer = BatchReportSerializer(objs, many=True)
        orgser = OrganizationShowSerializer(orgs, many=True)
        return Response({"data": serializer.data, 'orgs':orgser.data}, status=status.HTTP_200_OK)
    
    def generate_excel_file(self, df):
        wb = Workbook()
        ws = wb.active

        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)

        # Adjust column width based on the header length
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter  # Get the column name
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                        pass
                adjusted_width = max_length + 2
                ws.column_dimensions[column].width = adjusted_width

        # Save the workbook to an in-memory BytesIO buffer
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
                batch = BatchReport.objects.filter(id=ids)
            else:
                batch = BatchReport.objects.filter(id__in=ids)
                
            if not batch:
                return Response({"message": f"No data found!"}, status=status.HTTP_404_NOT_FOUND)
            dataframe = list(batch.values(
                'Cust_Id',
                'Sub_Id',
                'Vendor_Number',
                'Location_Code',
                'Payment_Comments',
                'Payment_Number',
                'Vendor_Name_1',
                'Vendor_Name_2',
                'Vendor_Address_1',
                'Vendor_Address_2',
                'Vendor_City',
                'Vendor_State',
                'Vendor_Zip',
                'Vendor_Country',
                'Vendor_Tax_Id',
                'Vendor_Phone_Number',
                'Customer_Vendor_Account_Number',
                'Payment_Misc_1',
                'Invoice_Number',
                'Total_Amount',
                'Adjustment_Amount',
                'Net_Amount',
                'Due_Date',
                'Invoice_Date',
                'Invoice_Comments',
                'Invoice_Misc_1'
            ))

            df = pd.DataFrame(dataframe)

            # Set the custom headings
            df.rename(columns={
                'Cust_Id': "Cust Id",
                'Sub_Id': "Sub Id",
                'Vendor_Number': "Vendor Number",
                'Location_Code': "Location Code",
                'Payment_Comments': "Payment Comments",
                'Payment_Number': "Payment Number",
                'Vendor_Name_1': "Vendor Name 1",
                'Vendor_Name_2': "Vendor Name 2",
                'Vendor_Address_1': "Vendor Address 1",
                'Vendor_Address_2': "Vendor Address 2",
                'Vendor_City': "Vendor City",
                'Vendor_State': "Vendor State",
                'Vendor_Zip': "Vendor Zip",
                'Vendor_Country': "Vendor Country",
                'Vendor_Tax_Id': "Vendor Tax Id",
                'Vendor_Phone_Number': "Vendor Phone Number",
                'Customer_Vendor_Account_Number': "Customer Vendor Account Number",
                'Payment_Misc_1': "Payment Misc 1",
                'Invoice_Number': "Invoice Number",
                'Total_Amount': "Total Amount",
                'Adjustment_Amount': "Adjustment Amount",
                'Net_Amount': "Net Amount",
                'Due_Date': "Due Date",
                'Invoice_Date': "Invoice Date",
                'Invoice_Comments': "Invoice Comments",
                'Invoice_Misc_1': "Invoice Misc 1"
            }, inplace=True)
            print(data)
            excel_buffer = self.generate_excel_file(df)

            obj = batch[0]
            folder = str(obj.output_file.path).split("/")
            folder.remove(folder[-1])
            folder = "/".join(folder)
            shutil.rmtree(folder)
            from_to = str(ids[0]) + '->' + str(ids[-1])
            file_name = f"batch_report_{from_to} .xlsx"
            file_path = os.path.join(settings.MEDIA_ROOT, "batchreports", file_name)
            
            # Save the file to Django's MEDIA storage
            obj.output_file.save(file_name, ContentFile(excel_buffer.getvalue()), save=True)
            if data["action"] == "download":
                return Response({"data": obj.output_file.url}, status=status.HTTP_200_OK)
            elif data['action'] == "send_mail":
                rm = data.get('to_mail')
                print("sending mail...")
                try:
                    send_custom_email(
                        receiver_mail=rm,
                        subject='Batch Report',
                        body='Please find the attached report.',
                        attachment=obj.output_file
                    )
                    return Response({"message":f"Email sent successfully sent to {rm}"}, status=status.HTTP_200_OK)
                except Exception as e:
                    print(e)
                    return Response({"message":f"Error in sending mail:{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"message":"Invalid action!"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id, *args, **kwargs):
        try:
            obj = BatchReport.objects.get(id=id)
            data = request.data
            if 'type' in data:
                if data['type'] == 'status-change':
                    obj.approved = data['status']
                    obj.approved_changer = request.user.designation.name        
                obj.save()
                saveuserlog(request.user, f'Changed approves of Batch Report with ID: {id} to {data["status"]}')
            else:
                serializer = BatchReportSerializer(obj, data=data, partial=True)
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
        
    def delete(self, request, id, *args, **kwargs):
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
