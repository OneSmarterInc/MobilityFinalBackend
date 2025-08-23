# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from django.conf import settings
# from django.core.files.base import ContentFile

# from OnBoard.Ban.models import BaseDataTable
# from Batch.models import BatchAutomation

# from OnBoard.Organization.models import Organizations
# from sendmail import send_custom_email
# from openpyxl import Workbook
# from openpyxl.utils.dataframe import dataframe_to_rows

# import pandas as pd
# from io import BytesIO

# class Command(BaseCommand):
#     help = "Automatically generate and email batch reports for scheduled automations"

#     def handle(self, *args, **options):
#         today = timezone.now().date()
#         weekday = timezone.now().strftime('%A')

#         self.stdout.write(f"[INFO] Running automation script for weekday: {weekday}")

#         # Manually filter due to SQLite limitations on JSONField lookups
#         all_automations = BatchAutomation.objects.all()
#         automations = []

#         for auto in all_automations:
#             for entry in auto.days:
#                 if entry.get("day") == weekday and entry.get("production", False):
#                     automations.append(auto)
#                     break

#         if not automations:
#             self.stdout.write(f"[INFO] No automations scheduled for {weekday}")
#             return

#         for automation in automations:
#             company_id = automation.company_id
#             emails = automation.emails or []

#             try:
#                 org = Organizations.objects.get(id=company_id)
#                 organization_name = org.Organization_name
#             except Organizations.DoesNotExist:
#                 self.stdout.write(f"[ERROR] Organization with ID {company_id} not found. Skipping.")
#                 continue

#             if not emails:
#                 self.stdout.write(f"[WARN] No emails configured for organization '{organization_name}'. Skipping.")
#                 continue

#             # Filter BaseDataTable records
#             data_qs = BaseDataTable.objects.filter(
#                 sub_company=organization_name,
#                 is_baseline_approved=True
#             ).exclude(viewuploaded=None, viewpapered=None)

#             if not data_qs.exists():
#                 self.stdout.write(f"[INFO] No data for organization '{organization_name}'. Skipping.")
#                 continue

#             self.stdout.write(f"[INFO] Found {data_qs.count()} entries for '{organization_name}'")

#             df = pd.DataFrame.from_records(data_qs.values())
#             if df.empty:
#                 self.stdout.write(f"[INFO] DataFrame empty after filtering. Skipping.")
#                 continue

#             # Drop unnecessary columns
#             drop_columns = [
#                 'created', 'updated','auto_pay_enabled','Entry_type','master_account', 'website',
#                 'Total_Current_Charges','plans','charges', 'location','duration','id', 'banUploaded_id',
#                 'Total_Amount_Due', 'banOnboarded_id', 'viewuploaded_id','viewpapered_id', 'inventory_id',
#                 'costcenterlevel', 'costcentertype','costcenterstatus', 'CostCenter', 'CostCenterNotes', 'PO',
#                 'Displaynotesonbillprocessing', 'POamt', 'FoundAcc', 'bantype','invoicemethod', 'vendorCS',
#                 'vendor_alias', 'month', 'year', 'pdf_filename', 'pdf_path', 'remarks', 'account_password',
#                 'payor', 'GlCode', 'ContractTerms', 'ContractNumber', 'Services','Billing_cycle', 'BillingDay',
#                 'PayTerm', 'AccCharge','CustomerOfRecord', 'contract_name', 'contract_file', 'paymentType',
#                 'billstatus', 'banstatus', 'Check', 'summary_file','is_baseline_approved','workbook_path',
#                 'batch_file','current_annual_review','previous_annual_review'
#             ]
#             df.drop(columns=[col for col in drop_columns if col in df.columns], inplace=True, errors='ignore')

#             # Rename columns for email
#             df.rename(columns={
#                 'bill_date': 'Bill Date',
#                 'date_due': 'Due Date',
#                 'accountnumber': 'Account Number',
#                 'invoicenumber': 'Invoice Number',
#                 'total_charges': 'Total Charges',
#                 'company': 'Company',
#                 'vendor': 'Vendor',
#                 'sub_company': 'Sub Company',
#                 'RemittanceAdd': 'Remittance Address',
#                 'BillingName': 'Billing Name',
#                 'BillingAdd': 'Billing Address',
#                 'BillingState': 'Billing State',
#                 'BillingZip': 'Billing Zip',
#                 'BillingCity': 'Billing City',
#                 'BillingCountry': 'Billing Country',
#                 'BillingAtn': 'Billing Attention',
#                 'BillingDate': 'Billing Date',
#                 'RemittanceName': 'Remittance Name',
#                 'RemittanceState': 'Remittance State',
#                 'RemittanceZip': 'Remittance Zip',
#                 'RemittanceCity': 'Remittance City',
#                 'RemittanceCountry': 'Remittance Country',
#                 'RemittanceAtn': 'Remittance Attention',
#                 'RemittanceNotes': 'Remittance Notes',
#                 'vendor_id': 'Vendor ID',
#                 'batch_approved': 'Batch Approved',
#                 'batch_approved_changer': 'Batch Approved By',
#                 'baseline_notes': 'Baseline Notes',
#                 'net_amount': 'Net Amount'
#             }, inplace=True)

#             # Generate Excel
#             excel_buffer = BytesIO()
#             wb = Workbook()
#             ws = wb.active

#             for r in dataframe_to_rows(df, index=False, header=True):
#                 ws.append(r)

#             for col in ws.columns:
#                 max_length = 0
#                 column = col[0].column_letter
#                 for cell in col:
#                     try:
#                         if len(str(cell.value)) > max_length:
#                             max_length = len(str(cell.value))
#                     except:
#                         pass
#                 ws.column_dimensions[column].width = max_length + 2

#             wb.save(excel_buffer)
#             excel_buffer.seek(0)

#             file_name = f"batch_report_{organization_name}_{today}.xlsx"

#             # Send emails
#             try:
#                 for receiver in emails:
#                     send_custom_email(
#                         receiver_mail=receiver,
#                         subject=f"Batch Report - {organization_name}",
#                         body="Please find the attached batch report for today.",
#                         attachment=ContentFile(excel_buffer.getvalue(), name=file_name)
#                     )
#                 self.stdout.write(f"[SUCCESS] Email sent to {emails} for organization '{organization_name}'")
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(
#                     f"[ERROR] Sending email failed for '{organization_name}': {e}"
#                 ))


from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from django.db import transaction

from OnBoard.Ban.models import BaseDataTable
from Batch.models import BatchAutomation
from OnBoard.Organization.models import Organizations

from sendmail import send_custom_email
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

import pandas as pd
from io import BytesIO


class Command(BaseCommand):
    
    help = "Automatically generate and email batch reports for scheduled automations"

    def handle(self, *args, **options):
        print("running command...")
        today = timezone.now().date()
        weekday = timezone.now().strftime('%A')

        self.stdout.write(f"[INFO] Running automation script for weekday: {weekday}")

        # Collect automations for this weekday (both preview and production)
        autos_today = []
        for auto in BatchAutomation.objects.all():
            for entry in (auto.days or []):
                if entry.get("day") == weekday:
                    prod_raw = entry.get("production", False)

                    # STRICT: only True (boolean) counts as production day
                    is_prod_day = (prod_raw is True)

                    # Debug line (safe to leave in or remove later)
                    self.stdout.write(f"[DBG] {auto.company_id} day={weekday} production_raw={prod_raw} type={type(prod_raw).__name__} -> is_prod_day={is_prod_day}")

                    autos_today.append((auto, is_prod_day))
                    break

        if not autos_today:
            self.stdout.write(f"[INFO] No automations scheduled for {weekday}")
            return

        for automation, is_prod_day in autos_today:
            company_id = automation.company_id
            emails = automation.emails or []

            try:
                org = Organizations.objects.get(id=company_id)
                organization_name = org.Organization_name
            except Organizations.DoesNotExist:
                self.stdout.write(f"[ERROR] Organization with ID {company_id} not found. Skipping.")
                continue

            if not emails:
                self.stdout.write(f"[WARN] No emails configured for '{organization_name}'. Skipping.")
                continue

            # Pending rows only
            data_qs = (
                BaseDataTable.objects
                .filter(
                    sub_company=organization_name,
                    is_baseline_approved=True,
                    is_production=False
                )
                .exclude(viewuploaded=None, viewpapered=None)
            )

            if not data_qs.exists():
                self.stdout.write(
                    f"[INFO] No pending rows for '{organization_name}' "
                    f"({'PRODUCTION' if is_prod_day else 'PREVIEW'}). Skipping."
                )
                continue

            self.stdout.write(
                f"[INFO] Found {data_qs.count()} pending rows for '{organization_name}' "
                f"({'PRODUCTION' if is_prod_day else 'PREVIEW'})"
            )

            # Build dataframe
            df = pd.DataFrame.from_records(data_qs.values())
            if df.empty:
                self.stdout.write("[INFO] DataFrame empty after filtering. Skipping.")
                continue

            drop_columns = [
                'created', 'updated','auto_pay_enabled','Entry_type','master_account', 'website',
                'Total_Current_Charges','plans','charges', 'location','duration','id', 'banUploaded_id',
                'Total_Amount_Due', 'banOnboarded_id', 'viewuploaded_id','viewpapered_id', 'inventory_id',
                'costcenterlevel', 'costcentertype','costcenterstatus', 'CostCenter', 'CostCenterNotes', 'PO',
                'Displaynotesonbillprocessing', 'POamt', 'FoundAcc', 'bantype','invoicemethod', 'vendorCS',
                'vendor_alias', 'month', 'year', 'pdf_filename', 'pdf_path', 'remarks', 'account_password',
                'payor', 'GlCode', 'ContractTerms', 'ContractNumber', 'Services','Billing_cycle', 'BillingDay',
                'PayTerm', 'AccCharge','CustomerOfRecord', 'contract_name', 'contract_file', 'paymentType',
                'billstatus', 'banstatus', 'Check', 'summary_file','is_baseline_approved','workbook_path',
                'batch_file','current_annual_review','previous_annual_review'
            ]
            df.drop(columns=[c for c in drop_columns if c in df.columns], inplace=True, errors='ignore')

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

            # Excel build
            excel_buffer = BytesIO()
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
                            max_length = len(str(cell.value))
                    except Exception:
                        pass
                ws.column_dimensions[column].width = max_length + 2
            wb.save(excel_buffer)
            excel_buffer.seek(0)

            file_name = f"batch_report_{organization_name}_{today}.xlsx"

            # Send and conditionally update
            try:
                with transaction.atomic():
                    for receiver in emails:
                        send_custom_email(
                            receiver_mail=receiver,
                            subject=f"Batch Report - {organization_name}",
                            body=f"Please find the attached batch report for {today} "
                                 f"({'PRODUCTION' if is_prod_day else 'PREVIEW'}).",
                            attachment=ContentFile(excel_buffer.getvalue(), name=file_name)
                        )

                    # Only flip on actual boolean True
                    if is_prod_day is True:
                        updated = data_qs.update(is_production=True)
                        self.stdout.write(
                            f"[SUCCESS] Sent {data_qs.count()} rows to {emails} "
                            f"and flagged {updated} as is_production=True."
                        )
                    else:
                        self.stdout.write(
                            f"[SUCCESS] Preview sent to {emails} for '{organization_name}'. "
                            f"Rows left with is_production=False."
                        )
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"[ERROR] Sending email failed for '{organization_name}': {e}"
                ))
