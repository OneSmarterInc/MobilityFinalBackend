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
# import permission classes

from openpyxl import Workbook
from sendmail import send_custom_email
# call update_or_create a django method
from .emails_verify import verify_smtp_login
from rest_framework.decorators import action
import ast
from io import BytesIO
from openpyxl.utils.dataframe import dataframe_to_rows
from rest_framework import viewsets, permissions
from .models import BatchAutomation
from .serializers import BatchAutomationSerializer
from django.core.files.base import ContentFile
from datetime import datetime, timedelta

from uuid import uuid4
from django.conf import settings
import os
import shutil
import pandas as pd
from django.forms import model_to_dict
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import EmailConfiguration
from .serializers import EmailConfigurationSerializer
from pandas.api.types import is_datetime64_any_dtype as is_datetime

from authenticate.views import saveuserlog
from authenticate.models import PortalUser
from django.db.models import Func, DateField, F, Q, Sum

class BatchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,org, *args, **kwargs):
        objs = BaseDataTable.objects.filter(sub_company=org).exclude(viewuploaded=None, viewpapered=None).filter(is_baseline_approved=True)
        serializer = BaseDataSerializer(objs, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
    
    def generate_excel_file(self, df):
        wb = Workbook()
        for col in df.columns:
            if is_datetime(df[col]):
                df[col] = df[col].dt.tz_localize(None)
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
    def filter_by_range(self,data, start, end):
        formatted_start = self.parse_custom_date(start) if start else None
        formatted_end = self.parse_custom_date(end) if end else None

        filtered_data = data.annotate(
            bill_date_parsed=Func(
            F('bill_date'),
            function='STRFTIME',
            template="DATE(STRFTIME('%%%%Y-%%%%m-%%%%d', %(expressions)s))",
            output_field=DateField(),
        )
        )

        if formatted_start:
            filtered_data = filtered_data.filter(bill_date_parsed__gte=formatted_start)
        if formatted_end:
            filtered_data = filtered_data.filter(bill_date_parsed__lte=formatted_end)

        return filtered_data
    
    def parse_custom_date(self, date_str):
        try:
            return datetime.strptime(date_str.strip(), "%b %d %Y").date()
        except:
            return None

    def post(self, request, *args, **kwargs):
        data = request.data
        if 'action' in data:
            org = data['sub_company']
            company = data['company']
            from_date = data['from_date']
            to_date = data['to_date']
            ids = ast.literal_eval(data['ids'])
            if type(ids) == int:
                base_ids = BaseDataTable.objects.filter(id=ids)
            else:
                base_ids = BaseDataTable.objects.filter(id__in=ids)
            
            base_ids = base_ids.exclude(batch_approved="Pending")
            base_ids = self.filter_by_range(data=base_ids, start=from_date, end=to_date)
            if not base_ids:
                return Response({"message": f"Data not found!"}, status=status.HTTP_404_NOT_FOUND)

            
            df = pd.DataFrame.from_records(base_ids.values())
            df = df.drop(columns=['created', 'updated','auto_pay_enabled','Entry_type','master_account', 'website', 'Total_Current_Charges','plans','charges', 'location','duration','id', 'banUploaded_id','Total_Amount_Due', 'banOnboarded_id', 'viewuploaded_id','viewpapered_id', 'inventory_id','costcenterlevel', 'costcentertype','costcenterstatus', 'CostCenter', 'CostCenterNotes', 'PO','Displaynotesonbillprocessing', 'POamt', 'FoundAcc', 'bantype','invoicemethod', 'vendorCS', 'vendor_alias', 'month', 'year',
            'pdf_filename', 'pdf_path', 'remarks', 'account_password','payor', 'GlCode', 'ContractTerms', 'ContractNumber', 'Services','Billing_cycle', 'BillingDay', 'PayTerm', 'AccCharge','CustomerOfRecord', 'paymentType',
            'billstatus', 'banstatus', 'Check', 'summary_file','is_baseline_approved','workbook_path','batch_file','current_annual_review',
            'previous_annual_review','variance','is_production','check_timestamp','is_baseline_replaced'])

            user_ids = df["uploaded_by_id"].dropna().unique()
            user_map = (
                PortalUser.objects
                .filter(id__in=user_ids)
                .values_list("id", "email")
            )

            user_map = dict(user_map)
            df["Uploaded by"] = df["uploaded_by_id"].map(user_map).fillna("Unknown User")
            df.drop(columns=["uploaded_by_id"], inplace=True)

            batch = base_ids
            
            

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
                'net_amount': 'Net Amount',
                "bill_approved_date": "Bill approved date"
            }, inplace=True)

            df['Bill approved date'] = df['Bill approved date'].dt.tz_localize(None)

            
            # empty all 
            folder_path = os.path.join(settings.MEDIA_ROOT, "batchfiles")
            shutil.rmtree(folder_path) if os.path.exists(folder_path) else None
            excel_buffer = self.generate_excel_file(df)
            obj = batch[0]

            file_name = f"batch_report_{org}.xlsx"
            obj.batch_file.save(file_name, ContentFile(excel_buffer.getvalue()), save=True)

            
            if data["action"] == "download":
                saveuserlog(request.user, f"Batch Report of organization {obj.sub_company} downloaded by user.")
                return Response({"data": obj.batch_file.url}, status=status.HTTP_200_OK)
            elif data['action'] == "send_mail":
                
                rm = data.get('to_mail')
                print("sending mail...")
                try:

                    send_custom_email(
                        company=company,                    
                        organization=org,                   
                        subject="Batch Report",
                        to=rm,                                 
                        body_text="Please find the attached report.",
                        attachments=[obj.batch_file],     
                    )
                    saveuserlog(request.user, f"Batch Report of organization {obj.sub_company} emailed to {rm}.")
                    return Response({"message":f"Email sent successfully sent to {rm}"}, status=status.HTTP_200_OK)
                except Exception as e:
                    print(e)
                    return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"message":"Invalid action!"}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request,org, id, *args, **kwargs):
        try:
            obj = BaseDataTable.objects.filter(id=id).first()
            if not obj:
                return Response({'message': 'Batch Report not found'}, status=status.HTTP_404_NOT_FOUND)
            data = request.data
            if 'type' in data:
                if data['type'] == 'status-change':
                    obj.batch_approved = data['status']
                    obj.batch_approved_changer = request.user.designation.name        
                obj.save()
                saveuserlog(
                    request.user,
                    f"Batch Report approval status changed for account {obj.accountnumber}, bill date {obj.bill_date} → {data['status']}"
                )


            else:
                serializer = BaseDataSerializer(obj, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    saveuserlog(request.user, f'Updated Batch Report for account {obj.accountnumber}, bill date {obj.bill_date}')
                    return Response({'message': 'Batch Report updated successfully'}, status=status.HTTP_200_OK)
                else:
                    print(serializer.errors)
                    return Response({"message" : "Unable to update batch."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'message': 'Batch Report updated successfully'}, status=status.HTTP_200_OK)
        except BatchReport.DoesNotExist:
            return Response({'message': 'Batch Report not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f'Error in Batch Report update: {e}')
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request,org, id, *args, **kwargs):
        try:
            obj = BatchReport.objects.get(id=id)
            acc = obj.Customer_Vendor_Account_Number
            bd = obj.billing_day
            obj.delete()
            saveuserlog(request.user, f'Deleted Batch Report for account {acc}, bill date {bd}')
            return Response({'message': 'Batch Report deleted successfully'}, status=status.HTTP_200_OK)
        except BatchReport.DoesNotExist:
            return Response({'message': 'Batch Report not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f'Error in Batch Report delete: {e}')
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class BatchAutomationViewSet(viewsets.ModelViewSet):
    queryset = BatchAutomation.objects.all()
    serializer_class = BatchAutomationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # supports ?company= or ?company_id=
        org_id = self.request.query_params.get("company") or self.request.query_params.get("company_id")
        if org_id:
            qs = qs.filter(company_id=org_id)  # <-- was organization_id
        freq = self.request.query_params.get("frequency")
        if freq:
            qs = qs.filter(frequency=freq)
        return qs
    
    


@api_view(['GET', 'POST'])
def email_config_list(request):
    from django.urls import resolve
    print('HIT email_config_list:', resolve(request.path_info))
    if request.method == 'GET':
        configs = EmailConfiguration.objects.all()
        serializer = EmailConfigurationSerializer(configs, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
         
        serializer = EmailConfigurationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            saveuserlog(request.user, description=f"Email configuration saved for organization {data['organization']}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Retrieve (GET one), Update (PUT), Delete (DELETE)
@api_view(['GET', 'PUT', 'DELETE'])
def email_config_detail(request, pk):
    config = get_object_or_404(EmailConfiguration, pk=pk)

    if request.method == 'GET':
        serializer = EmailConfigurationSerializer(config)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = EmailConfigurationSerializer(config, data=request.data, partial=True)  
        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            saveuserlog(request.user, description=f"Email configuration updated for organization {data['organization']}")
            # create_notification(request.user, msg=f"Email configuration updated for organization {data['organization']}",company=request.user.company)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        org = config.organization
        config.delete()
        saveuserlog(request.user, description=f"Email configuration deleted for organization {org}")
        return Response({'message': 'Deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    
    
    
class EmailConfigurationViewSet(viewsets.ModelViewSet):
    queryset = EmailConfiguration.objects.all()
    # serializer_class = ...  # your existing serializer

    @action(detail=False, methods=["post"], url_path="verify")
    def verify(self, request):
        """
        Accepts either a full config payload OR a config id to reuse stored password.
        Body:
          - company, organization, sender_email, smtp_username (optional), smtp_host, smtp_port, use_ssl, use_tls
          - password (optional if id provided)
          - id (optional) -> when present and password missing, use stored password for that row
        """
        data = request.data
        config_id = data.get("id")
        password = (data.get("password") or "").strip()

        # pull from DB if id present
        cfg = None
        if config_id:
            cfg = EmailConfiguration.objects.filter(id=config_id).first()
            if not cfg:
                return Response({"ok": False, "message": "Config not found."},
                                status=status.HTTP_404_NOT_FOUND)
            if not password:
                password = (cfg.password or "").strip()

        # gather fields (prefer request body; fallback to cfg)
        def pick(key, default=None):
            if key in data and data[key] not in (None, ""):
                return data[key]
            return getattr(cfg, key, default) if cfg else default

        smtp_host = pick("smtp_host")
        smtp_port = pick("smtp_port")
        sender_email = pick("sender_email")
        smtp_username = pick("smtp_username") or sender_email  # login default
        use_ssl = bool(pick("use_ssl", False))
        use_tls = bool(pick("use_tls", True))

        # normalize common mismatches
        try:
            smtp_port = int(smtp_port)
        except Exception:
            return Response({"ok": False, "message": "smtp_port must be an integer."},
                            status=status.HTTP_400_BAD_REQUEST)

        if smtp_port == 465:
            use_ssl, use_tls = True, False
        elif smtp_port == 587:
            use_tls, use_ssl = True, False
        if use_ssl and use_tls:
            # prefer SSL on 465, TLS otherwise
            use_ssl = (smtp_port == 465)
            use_tls = not use_ssl

        # required checks
        missing = [k for k, v in {
            "smtp_host": smtp_host, "smtp_port": smtp_port,
            "sender_email": sender_email, "password": password
        }.items() if not v]
        if missing:
            return Response({"ok": False, "message": f"Missing fields: {', '.join(missing)}"},
                            status=status.HTTP_400_BAD_REQUEST)

        ok, msg = verify_smtp_login(
            host=smtp_host, port=smtp_port,
            username=(smtp_username or sender_email),
            password=password,
            use_tls=use_tls, use_ssl=use_ssl,
        )
        code = status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST
        saveuserlog(request.user, description=f"Email configure verification done for organization")
        return Response({
            "ok": ok,
            "message": msg,
            "normalized": {
                "use_ssl": use_ssl, "use_tls": use_tls, "smtp_port": smtp_port
            }
        }, status=code)    


from .models import Notification
from .ser import NotificationSerializer, NotificationSaveSerializer
from rest_framework.decorators import api_view, permission_classes

def create_notification(user, msg, company=None):
    data={
        "company_key":company.id if company else None,
        "company":company.Company_name if company else "",
        "user":user.id if user else None,
        "description":msg
    }
    print(data)
    ser = NotificationSaveSerializer(data=data)
    if ser.is_valid():
        ser.save()
    else:
        print("Error saving notification",ser.errors)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notifications_by_company(request,*args, **kwargs):
    """
    GET /api/notifications?company_id=OneSmarter
    """
    qs = Notification.objects.filter(user=request.user) if request.user.company else Notification.objects.all()
    qs = qs.order_by("-created_at")
    data = NotificationSerializer(qs, many=True).data
    return Response({"data": data}, status=status.HTTP_200_OK)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_notification(request, pk: int):
    """
    DELETE /api/notifications/<id>/
    """
    try:
        n = Notification.objects.get(pk=pk)
    except Notification.DoesNotExist:
        return Response(status=status.HTTP_204_NO_CONTENT)  # idempotent delete

    n.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_all_notification(request):
    try:
        n = Notification.objects.filter(company_key=request.user.company) if request.user.company else Notification.objects.all()
    except Notification.DoesNotExist:
        return Response(status=status.HTTP_204_NO_CONTENT)  # idempotent delete

    n.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)