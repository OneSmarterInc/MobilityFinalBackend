from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile

from OnBoard.Ban.models import BaseDataTable
from Batch.models import BatchAutomation
from OnBoard.Organization.models import Organizations

from sendmail import send_custom_email
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

import pandas as pd
from io import BytesIO
import calendar
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate and email batch reports based on automation frequency"

    def handle(self, *args, **options):
        today = timezone.now().date()
        weekday = today.strftime("%A")
        day_of_month = today.day

        self.stdout.write(f"[INFO] Running batch automation for {today} ({weekday})")
        self.org = None
        automations_to_run = []

        for auto in BatchAutomation.objects.all():
            freq = auto.frequency

            # ---------------- DAILY ----------------
            if freq == "daily":
                automations_to_run.append((auto, True))
                continue

            # ---------------- WEEKLY ----------------
            if freq == "weekly":
                for entry in (auto.days or []):
                    if entry.get("day") == weekday:
                        prod = entry.get("production", False)
                        if not isinstance(prod, bool):
                            raise ValueError(
                                f"Invalid production flag for weekly automation {auto.id}"
                            )
                        automations_to_run.append((auto, prod))
                        break

            # ---------------- SPECIFIC ----------------
            elif freq == "specific":
                last_day = calendar.monthrange(today.year, today.month)[1]

                for entry in (auto.dates or []):
                    date_value = entry.get("date")

                    if not isinstance(date_value, int):
                        raise ValueError(
                            f"Invalid date value for automation {auto.id}"
                        )

                    # Skip invalid dates like 31 in Feb
                    if date_value > last_day:
                        continue

                    if date_value == day_of_month:
                        prod = entry.get("production", False)
                        if not isinstance(prod, bool):
                            raise ValueError(
                                f"Invalid production flag for specific automation {auto.id}"
                            )
                        automations_to_run.append((auto, prod))
                        break

        if not automations_to_run:
            self.stdout.write("[INFO] No automations scheduled today.")
            return

        # ---------------- PROCESS AUTOMATIONS ----------------
        for automation, is_prod_day in automations_to_run:
            try:
                self.org = Organizations.objects.get(id=automation.company_id)
            except Organizations.DoesNotExist:
                self.stdout.write(
                    f"[ERROR] Organization {automation.company_id} not found."
                )
                continue

            if not automation.emails:
                self.stdout.write(
                    f"[WARN] No emails configured for {self.org.Organization_name}"
                )
                continue

            qs = (
                BaseDataTable.objects.exclude(viewuploaded=None, viewpapered=None)
                .filter(
                    sub_company=self.org.Organization_name,
                    is_baseline_approved=True,
                    is_production=False
                )
            )
            if not qs.exists():
                self.stdout.write(
                    f"[INFO] No pending data for {self.org.Organization_name}"
                )
                continue

            df = pd.DataFrame.from_records(qs.values())
            if df.empty:
                self.stdout.write("[INFO] DataFrame empty after queryset.")
                continue

            # -------- WHITELIST COLUMNS (SAFE) --------
            allowed_columns = [
                "bill_date", "date_due", "accountnumber",
                "invoicenumber", "total_charges", "vendor",
                "sub_company", "net_amount"
            ]
            df = df[[c for c in allowed_columns if c in df.columns]]

            df.rename(columns={
                "bill_date": "Bill Date",
                "date_due": "Due Date",
                "accountnumber": "Account Number",
                "invoicenumber": "Invoice Number",
                "total_charges": "Total Charges",
                "vendor": "Vendor",
                "sub_company": "Sub Company",
                "net_amount": "Net Amount"
            }, inplace=True)

            # -------- EXCEL GENERATION --------
            excel_buffer = BytesIO()
            wb = Workbook()
            ws = wb.active

            for row in dataframe_to_rows(df, index=False, header=True):
                ws.append(row)

            for col in ws.columns:
                max_len = max(len(str(cell.value)) if cell.value else 0 for cell in col)
                ws.column_dimensions[col[0].column_letter].width = max_len + 2

            wb.save(excel_buffer)

            filename = f"batch_report_{self.org.Organization_name}_{today}.xlsx"
            attachment = ContentFile(excel_buffer.getvalue(), name=filename)

            # -------- EMAIL --------
            try:
                send_custom_email(
                    company=self.org.company.Company_name,
                    to=automation.emails,
                    subject=f"Batch Report - {self.org.Organization_name}",
                    body_text=(
                        f"Attached is the batch report for {today} "
                        f"({'PRODUCTION' if is_prod_day else 'PREVIEW'})."
                    ),
                    attachments=[attachment]
                )

                if is_prod_day:
                    updated = qs.update(is_production=True)
                    self.stdout.write(
                        f"[SUCCESS] PRODUCTION sent for {self.org.Organization_name}. "
                        f"{updated} rows marked as production."
                    )
                else:
                    self.stdout.write(
                        f"[SUCCESS] PREVIEW sent for {self.org.Organization_name}."
                    )

            except Exception as e:
                logger.exception(e)
                self.stdout.write(
                    self.style.ERROR(
                        f"[ERROR] Failed sending email for {self.org.Organization_name}: {e}"
                    )
                )
