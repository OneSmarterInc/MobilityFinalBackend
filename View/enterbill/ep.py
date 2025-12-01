import pandas as pd
import json
import time
from OnBoard.Ban.models import PdfDataTable, UniquePdfDataTable, BaseDataTable, BaselineDataTable
import re
import numpy as np
import json
from OnBoard.Company.models import Company
from authenticate.models import PortalUser
from Batch.views import create_notification
from baselineTag import object_tagging
from django.utils import timezone
from django.conf import settings
from addon import get_cat_obj_total
from ..models import ProcessedWorkbook
from django.core.files import File

import os, io

class EnterBillProcessExcel:
    def __init__(self, buffer_data,instance,typeofupload=None):

        print("init")
        self.instance = instance
        self.buffer_data = json.loads(buffer_data) if isinstance(buffer_data, str) else buffer_data
        print(type(self.buffer_data))
        self.type = typeofupload
        self.company = self.buffer_data.get('company')
        self.vendor = self.buffer_data.get('vendor')
        self.account_number = self.buffer_data.get('account_number')
        self.sub_company = self.buffer_data.get('sub_company')
        self.mapping_data = self.buffer_data.get('mapping_json')
        self.excel_csv_path = self.buffer_data.get('excel_csv_path')
        self.entry_type = self.buffer_data.get('entry_type')
        self.master_account = self.buffer_data.get('master_account')
        self.location = self.buffer_data.get('location')
        self.month = self.buffer_data.get('month')
        self.year = self.buffer_data.get('year')
        self.email = self.buffer_data.get('email')
        self.invoice_number = None
        self.net_amount = None
        self.user_obj = PortalUser.objects.filter(email=self.email).first()
        self.company_obj = Company.objects.filter(Company_name=self.company).first()
        if "verizon" in self.vendor:
            self.website = "http://sso.verizonenterprise.com"
            self.remittance_add = "PO BOX 489 NEWARK, NJ 07101-0489"
        elif "mobile" in self.vendor:
            self.website = "http://www.business.att.com/"
            self.remittance_add = "PO BOX 742596 CINCINNATI, OH 45274-2596"
            
        else:
            self.website = "https://www.t-mobile.com/"
            self.remittance_add = "PO Box 6463 Carol Stream, IL 60197-6463"

        print("init complete")

    def format_wireless_number(self, number):
        pattern2 = r'^\d{3}\-\d{3}\-\d{4}$'
        if len(str(number)) <= 10:
            return
        if re.match(pattern2, str(number)):
            return number
        pattern = r'^\d{3}\.\d{3}\.\d{4}$'
        
        if re.match(pattern, str(number)):
            return str(number).replace('.','-')
        
        cleaned_number = str(number).replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
        cleaned_number = '-'.join(cleaned_number.split('-'))
        formatted_number = cleaned_number[:3] + "-" + cleaned_number[3:6] + "-" + cleaned_number[6:]
        return formatted_number
    
    def create_category_object(self, plan, monthly_charges):
        res = {}
        if not plan:
            return {}
        matches = list(re.finditer(r'\$(\d*\.?\d+)', plan))

        if matches:
            for i, match in enumerate(matches):
                amount = float(match.group(1))

                # Determine description boundaries
                start = matches[i-1].end() if i > 0 else 0
                end = match.start()

                desc = plan[start:end].strip().upper()

                # Remove leading/trailing garbage words
                desc = re.sub(r'^\d[\d\.]*\s*', '', desc).strip()

                res[desc] = amount
        else:
            res[plan] = monthly_charges

        # Wrap inside Monthly Charges
        return json.dumps({"Monthly Charges": res})
    
    def reflect_category_object(self, bill_main_id):
        uniques = UniquePdfDataTable.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
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

    def reflect_uniquetable_non_bill_data(self,onboarded_id,bill_main_id):
        current_bill = UniquePdfDataTable.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        uploaded_baseline = UniquePdfDataTable.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
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
            sub_company=self.sub_company,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        uploaded_baseline = BaselineDataTable.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
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

    def add_tag_to_dict(self, bill_main_id, variance):
        print("def add_tag_to_dict")
        baseline = BaselineDataTable.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=None,
            viewpapered=None
        )

        current_bill = BaselineDataTable.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        print("length of baseline",len(baseline))

        print("length of current_bill",len(current_bill))
        baseline_dict = {b.Wireless_number: b for b in baseline if b.Wireless_number}
        for bill_obj in current_bill:
            wireless = bill_obj.Wireless_number
            baseline_obj = baseline_dict.get(wireless)
            if baseline_obj:  
                tagged_object = object_tagging(baseline_obj.category_object, bill_obj.category_object, variance)
                bill_obj.category_object = tagged_object
                bill_obj.save()

    def check_true_false(self, cat):
        formatted = json.loads(cat) if isinstance(cat, str) else cat
        for key, value in formatted.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict):
                        if sub_value['approved'] == False:
                            return False
        return True
    
    def check_baseline_approved(self, model,bill_main_id):
        all_objects = model.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        for line in all_objects:
            line.is_baseline_approved = self.check_true_false(line.category_object)
            line.save()

    def check_total_under_variance(self,bill_main_id,variance):
        baseline = BaselineDataTable.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=None,
            viewpapered=None
        )
        current_bill = BaselineDataTable.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        baseline_dict = {b.Wireless_number: b for b in baseline if b.Wireless_number}
        for bill_obj in current_bill:
            wireless = bill_obj.Wireless_number
            baseline_obj = baseline_dict.get(wireless)
            if baseline_obj:  
                baseline_total = get_cat_obj_total(baseline_obj.category_object)
                bill_total = get_cat_obj_total(bill_obj.category_object)
                lower, upper = bill_total * (1-variance/100), bill_total*(1+variance/100)
                check = lower <= baseline_total <= upper
                bill_obj.category_object = self.make_true_all(bill_obj.category_object) if check else bill_obj.category_object
                bill_obj.save()

    def make_true_all(self, cat):
        formatted = json.loads(cat) if isinstance(cat, str) else cat
        for key, value in formatted.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict):
                        sub_value['approved'] = True
        return json.dumps(formatted)
    
    def make_sheet2(self, df):
        print("make_sheet2")
        cols = [
            "Account Number", "Wireless Number", "User name",
            "Cost Center", "User email", "User status",
            "Plan", "Monthly Charges"
        ]
        return df[cols]
    def make_sheet3(self, df):
        print("make_sheet3")
        # Convert JSON strings to dictionary
        df2 = df.copy()
        print(df2.head())
        df2["category_object"] = df2["category_object"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )
        print(df2.head())
        # Normalize category_object
        rows = []
        for _, row in df2.iterrows():
            for cat, items in row["category_object"].items():
                print(row)
                for desc, amt in items.items():
                    rows.append({
                        "Account Number": row["Account Number"],
                        "Wireless Number": row["Wireless Number"],
                        "User name": row["User name"],
                        "Cost Center": row["Cost Center"],
                        "Item Category": cat,
                        "Item Description": desc,
                        "Charges": amt,
                    })

        return pd.DataFrame(rows)
    
    def make_sheet4(self,df):
        print("make_sheet4")
        # First build the exploded structure (similar to sheet3)
        s3 = self.make_sheet3(df)

        # Add Total Charges per wireless_number
        totals = s3.groupby("Wireless Number")["Charges"].sum().reset_index()
        totals.rename(columns={"Charges": "Total Charges"}, inplace=True)

        # Merge totals back
        merged = s3.merge(totals, on="Wireless Number", how="left")

        # Grand total (sum of all charges)
        self.net_amount = merged["Charges"].sum()

        # Add grand total column
        merged["Sum of Total Charges"] = self.net_amount

        # Final required sheet4 format
        return merged[[
            "Account Number",
            "Wireless Number",
            "Cost Center",
            "User name",
            "Total Charges",
            "Sum of Total Charges"
        ]].drop_duplicates()


    def get_db_df(self):
        print("def get_db_df")
        db_data = UniquePdfDataTable.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
            vendor=self.vendor,
            account_number=self.account_number,
            viewuploaded=None,
            viewpapered=None
        )
        if db_data.exists():
            datadf = pd.DataFrame(db_data.values("account_number","wireless_number", "cost_center", "User_email","user_name", "User_status", "plans", "monthly_charges", "category_object"))
            datadf = datadf.rename(columns={
                "account_number":"Account Number",
                "wireless_number": "Wireless Number",
                "cost_center": "Cost Center",
                "User_email": "User email",
                "User_status": "User status",
                "plans": "Plan",
                "user_name":"User name",
                "monthly_charges":"Monthly Charges"
            })
        else:
            return None, None, None

        sheet2 = self.make_sheet2(datadf)
        sheet3 = self.make_sheet3(datadf)
        sheet4 = self.make_sheet4(datadf)

        return sheet2, sheet3, sheet4
    
    def dataframe_to_excel(self, df1, df2, df3, df4):
        print("def dataframe_to_excel")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df1.to_excel(writer, sheet_name='Sheet1', index=False)
            df2.to_excel(writer, sheet_name='Sheet2', index=False)
            df3.to_excel(writer, sheet_name='Sheet3', index=False)
            df4.to_excel(writer, sheet_name='Sheet4', index=False)
        output.seek(0)
        return output
    
    def process_excel(self):
        print("process excel")
        df_csv = pd.read_excel(self.excel_csv_path)
        print("length of csv",len(df_csv))
        df_csv.columns = df_csv.columns.str.strip()
        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

        latest_entry_dict = self.mapping_data.copy()

        for key, value in latest_entry_dict.items():
            latest_entry_dict[key] = str(value).replace(' ', '_')
            
        column_mapping = {v: k for k, v in latest_entry_dict.items()}
        filtered_mapping = {key: value for key, value in column_mapping.items() if key != 'NA'}

        for key, value in latest_entry_dict.items():
            if value == "NA":
                latest_entry_dict[key] = key
        
        columns_to_keep = [col for col in latest_entry_dict.values() if col in df_csv.columns]
        df_csv = df_csv[columns_to_keep]
        df_csv.rename(columns=filtered_mapping, inplace=True)
        df_csv.replace('', np.nan, inplace=True)

        # Drop rows with any NaN (i.e., blank cells)
        df_csv.dropna(how='all', inplace=True)
        print("new df csv====",len(df_csv))
        print(df_csv)
        rw = df_csv.iloc[0]
        base_dict = rw.to_dict()

        print(base_dict)
        file_vendor = base_dict.get('vendor')
        file_account_number = base_dict.get('account_number')
        file_bill_date = base_dict.get('bill_date')

        if file_vendor != self.vendor:
            return {"message":f"Input vendor {self.vendor} not matched with excel vendor {file_vendor}!", 'code':1}

        print("vendor checked")
        print(file_account_number, self.account_number)
        if str(file_account_number) != str(self.account_number):
            return {"message":f"Input account number {self.account_number} not matched with excel account number {file_account_number}!", 'code':1}

        print("account number checked")
        check_ban = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(accountnumber=file_account_number)
        if not check_ban.exists():
            return {"message":f"Account number {file_account_number} not found!", 'code':1}
        
        print("account number presence checked")
        
        bill_date = file_bill_date.replace(",","").split(" ")
        print(bill_date)
        file_bill_date = " ".join(bill_date)

        if not (bill_date[0] in str(self.month)):
            return {'message' : f'Bill date from the excel file did not matched with input month', 'code' : 1}
        print("month checked")
        if self.year != bill_date[2]:
            return {'message' : f'Bill date from the excel file did not matched with input year', 'code' : 1}
        print("year checked")
        if BaseDataTable.objects.filter(accountnumber=file_account_number, company=self.company, sub_company=self.sub_company, month=self.month, year=self.year).exists():
            return {'message' : f'Bill already exists for account number {file_account_number}', 'code' : 1}
        
        print("existance checked")
        print(base_dict)
        base_dict['company'] = self.company
        base_dict['vendor'] = self.vendor
        base_dict['sub_company'] = self.sub_company
        base_dict['accountnumber'] = base_dict['account_number']

        base_dict['Entry_type'] = self.entry_type
        base_dict['location'] = self.location
        base_dict['master_account'] = self.master_account
        base_dict['bill_date'] = file_bill_date
        self.invoice_number = base_dict["invoice_number"]
        base_dict["invoicenumber"] = self.invoice_number
        
        keys_to_keep = ['company', 'vendor', 'sub_company', 'accountnumber', 'Entry_type', 'location', 'master_account','bill_date','invoicenumber']
        b_dict = {key: base_dict[key] for key in keys_to_keep if key in base_dict}
        

        onboarded = BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).filter(sub_company=self.sub_company, vendor=self.vendor, accountnumber=self.account_number).first()
        # Insert into BaseDataTable
        baseinstance = BaseDataTable.objects.create(viewuploaded=self.instance,month=self.month, year=self.year,RemittanceAdd=onboarded.RemittanceAdd,uploaded_by=PortalUser.objects.filter(email=self.email).first(), **b_dict)
        print("Data added to BaseDataTable")
        baseinstance.variance = onboarded.variance
        baseinstance.save()
        
        df_csv['wireless_number'] = df_csv['wireless_number'].apply(self.format_wireless_number)
        df_csv_dict = df_csv.to_dict(orient='records')
        df_csv_dict = [item for item in df_csv_dict if item.get("wireless_number")]
        
        for item in df_csv_dict:
            print(item)
            item['company'] = self.company
            item['bill_date'] = file_bill_date
            item['vendor'] = self.vendor
            item['sub_company'] = self.sub_company
            item['account_number'] = self.account_number
            item['entry_type'] = self.entry_type

            plan = item.get("Plan_name")
            item["plans"] = plan
            monthly_charges = item.get("monthly_charges")
            item["category_object"] = self.create_category_object(plan, monthly_charges)
        # Bulk insert into UniquePDFDataTable

        model_fields = [field.name for field in UniquePdfDataTable._meta.get_fields() if field.concrete and not field.auto_created]

        clean_items = [
            UniquePdfDataTable(viewuploaded=self.instance, **{k: v for k, v in item.items() if k in model_fields})
            for item in df_csv_dict
        ]
        UniquePdfDataTable.objects.bulk_create(clean_items)
        print("Data added to UniquePdfDataTable")

        df_csv = pd.DataFrame(df_csv_dict)
        df_csv = df_csv.rename(columns={'wireless_number': 'Wireless_number'})

        df_csv_dict = df_csv.to_dict(orient='records')

        model_fields = [field.name for field in BaselineDataTable._meta.get_fields() if field.concrete and not field.auto_created]

        clean_items = [
            BaselineDataTable(viewuploaded=self.instance, **{k: v for k, v in item.items() if k in model_fields})
            for item in df_csv_dict
        ]
        bill_main_id = baseinstance.viewuploaded.id
        onboarded_id = onboarded.banOnboarded
        
        BaselineDataTable.objects.bulk_create(clean_items)

        self.reflect_category_object(bill_main_id)
        self.reflect_baselinetable_non_bill_data(bill_main_id=bill_main_id, onboarded_id=onboarded_id)
        self.reflect_uniquetable_non_bill_data(bill_main_id=bill_main_id, onboarded_id=onboarded_id)

        self.add_tag_to_dict(bill_main_id, onboarded.variance)
        self.check_total_under_variance(bill_main_id=bill_main_id, variance=onboarded.variance)
        self.check_baseline_approved(UniquePdfDataTable, bill_main_id)
        self.check_baseline_approved(BaselineDataTable, bill_main_id)
        account_obj = BaselineDataTable.objects.filter(sub_company=self.sub_company, vendor=self.vendor, account_number=self.account_number).filter(viewuploaded=self.instance)
        approved_wireless_list = account_obj.values_list('is_baseline_approved', flat=True)

        is_approved = False if False in list(approved_wireless_list) else True
        baseinstance.is_baseline_approved = is_approved
        baseinstance.bill_approved_date = timezone.now()
        baseinstance.save()
        

        sheet1 = {"Company":self.company, "Sub Company":self.sub_company, "Vendor":self.vendor, "Website":self.website, "Remittance Address":self.remittance_add, "Account Number":self.account_number, "Invoice number":self.invoice_number, "Bill Date":file_bill_date, "Month":self.month, "Year":self.year, "Total Amount":None, "Due date":None, "Billing Name":None, "Billing Address":None}

        
        sheet2, sheet3, sheet4 = self.get_db_df()

        sheet1["Total Amount"] = f"${self.net_amount}"

        sheet1 = pd.DataFrame([sheet1])
        
        workbook = self.dataframe_to_excel(sheet1, sheet2, sheet3, sheet4)
        workbook_name = f"{self.account_number}_{self.month}_{self.year}.xlsx"
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
                sub_company_name=self.sub_company,
                workbook_name=workbook_name,
                bill_date_info=file_bill_date
            )
            
            # Open the saved file and keep it open for Django
            f = open(output_file_path, "rb")  # DO NOT USE `with open(...)`
            django_file = File(f, name=workbook_name)

            processed_workbook.output_file = django_file
            self.instance.output_file = django_file
            
            processed_workbook.save()
            self.instance.save()
            baseinstance.workbook_path = processed_workbook.output_file.url
            baseinstance.save()

            f.close()

        except Exception as e:
            print(e)
            message = str(e).strip()
        create_notification(user=self.user_obj, msg=f"Bill with date {bill_date} of ban {self.account_number} uploaded.",company=self.company_obj)
        return {"message":"Bill uploaded successully", 'code':0}

