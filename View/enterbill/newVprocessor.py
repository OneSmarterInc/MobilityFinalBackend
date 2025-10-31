from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable, BaselineDataTable, PdfDataTable, PortalInformation
import logging
import pdfplumber
from Scripts.VerizonNew import VerizonClass
from Scripts.AttNew import AttClass
from Scripts.Tmobile1New import Tmobile1Class
from Scripts.Tmobile2New import Tmobile2Class
import pandas as pd
import io
import json
import os
from django.conf import settings
from ..models import ProcessedWorkbook
from django.core.files import File
logging.basicConfig(level=logging.INFO)
from baselineTag import object_tagging
from addon import get_cat_obj_total
from OnBoard.Company.models import Company
from authenticate.models import PortalUser
from django.utils import timezone
from View.models import BillSummaryData, BillAnalysisData
from django.db import transaction

from Batch.views import create_notification
logger = logging.getLogger(__name__)

from dateutil import parser
import re
class ProcessPdf2:
    def __init__(self, buffer_data,btype,instance=None):
        self.instance = instance
        self.buffer_data = buffer_data
        self.pdf_path = self.buffer_data.get('pdf_path')
        self.company_name = self.buffer_data.get('company_name')
        self.vendor_name = self.buffer_data.get('vendor_name')
        self.pdf_filename = self.buffer_data.get('pdf_filename')
        self.month = self.buffer_data.get('month')
        self.entry_type = self.buffer_data.get('entry_type')
        self.baseline_check = str(self.buffer_data.get('baseline_check')).lower() == 'true'
        self.location = self.buffer_data.get('location')
        self.master_account = self.buffer_data.get('master_account')
        self.year = self.buffer_data.get('year')
        self.type = self.buffer_data.get('types')
        self.email = self.buffer_data.get('email')
        self.sub_company = self.buffer_data.get('sub_company_name')
        self.t_mobile_type = btype if btype else 0

        logger.info(f'Processing PDF from buffer: {self.pdf_path}, {self.company_name}, {self.vendor_name}, {self.pdf_filename}')

        self.user_obj = PortalUser.objects.filter(email=self.email).first()
        self.company_obj = Company.objects.filter(Company_name=self.company_name).first()

        self.bill_date = None
        self.net_amount = 0
        self.check = True
        self.account_number = None

        
    def base_data_table(self, data):
        baseDatamapped = {
            "accountnumber": data.get("Account Number"),
            "invoicenumber": data.get("Invoice Number"),
            "bill_date": data.get("Bill Date"),
            "date_due": data.get("Due Date"),
            "net_amount": str(data.get("Total Amount")).replace("$","").replace(",",""),
            "BillingName" : data.get("Billing Info").get("name"),
            "BillingAdd": data.get("Billing Info").get("address"),
            "RemittanceAdd": data.get("Remittance Info"),
            "total_charges":data.get("Total Charges"),
            "BillingAtn" : data.get("Billing Info").get("attn"),
            "website":  data.get("Vendor Url"),
            "duration": data.get("Duration"),
            "pdf_path": self.pdf_path,
            "pdf_filename": self.pdf_filename,
            "viewuploaded": self.instance,
            "sub_company": self.sub_company,
            "vendor": self.vendor_name,
            "company": self.company_name,
            "location": self.location,
            "master_account": self.master_account,
            "Entry_type":self.entry_type
        }
        obj = BaseDataTable.objects.create(**baseDatamapped)
        return obj
        
        print("Added to base data table")
    def pdf_data_table(self, datadf):
        pdf_mapping = {
            'Wireless Number': "wireless_number",
            'Username': "user_name", 
            'Data Usage':"data_usage", 
            'Message Usage':"messaging_usage",
            'Voice Plan Usage':"voice_plan_usage", 
            'Total Charges':"total_charges",
            'Third Party Charges (includes Tax)':"third_party_charges_includes_tax",
            'Taxes, Governmental Surcharges and Fees':"taxes_governmental_surcharges_and_fees",
            "Government fees and taxes": "taxes_governmental_surcharges_and_fees",
            'Surcharges and Other Charges and Credits':"surcharges_and_other_charges_credits", 
            "Company fees and surcharges":"surcharges_and_other_charges_and_credits",
            'Equipment Charges':"equipment_charges",
            'Usage and Purchase Charges':"usage_and_purchase_charges", 
            'Monthly Charges': "monthly_charges",
            "Item Category": "item_category",
            "Item Description": "item_description",
            "Charges": "item_charges",
            "Plans": "plans",
            "Group":"group_number",
            "Taxes and Surcharges": "taxes_governmental_surcharges_and_fees",
            "Third Party Services":"third_party_charges_includes_tax",
            "Usage Charges": "usage_and_purchase_charges", 
            "Credits & Adjustments": "surcharges_and_other_charges_and_credits",
        }
        datadf = datadf.rename(columns=pdf_mapping)
        datadf["company"] = self.company_name
        datadf["sub_company"] = self.sub_company
        datadf["vendor"] = self.vendor_name
        datadf["account_number"] = self.account_number
        datadf["bill_date"] = self.bill_date
        datadf["viewuploaded"] = self.instance
        datadf["location"] = self.location


        model_fields = [f.name for f in PdfDataTable._meta.fields]
        for _, row in datadf.iterrows():
            data = {field: row[field] for field in model_fields if field in row}
            PdfDataTable.objects.create(**data)

        print("Added to pdf data table")


    def unique_data_table(self, datadf):
        unique_mapping = {
            'Wireless Number': "wireless_number",
            'Username': "user_name", 
            'Data Usage':"data_usage", 
            'Message Usage':"messaging_usage",
            'Voice Plan Usage':"voice_plan_usage", 
            'Total Charges':"total_charges",
            'Third Party Charges (includes Tax)':"third_party_charges_includes_tax",
            'Taxes, Governmental Surcharges and Fees':"taxes_governmental_surcharges_and_fees",
            "Government fees and taxes": "taxes_governmental_surcharges_and_fees",
            'Surcharges and Other Charges and Credits':"surcharges_and_other_charges_credits", 
            "Company fees and surcharges":"surcharges_and_other_charges_and_credits",
            'Equipment Charges':"equipment_charges",
            'Usage and Purchase Charges':"usage_and_purchase_charges", 
            'Monthly Charges': "monthly_charges",
            "Plans": "plans",
            "Group":"group_number",
            "Taxes and Surcharges": "taxes_governmental_surcharges_and_fees",
            "Third Party Services":"third_party_charges_includes_tax",
            "Usage Charges": "usage_and_purchase_charges", 
            "Credits & Adjustments": "surcharges_and_other_charges_and_credits",

        }
        datadf = datadf.rename(columns=unique_mapping)
        datadf["company"] = self.company_name
        datadf["sub_company"] = self.sub_company
        datadf["vendor"] = self.vendor_name
        datadf["account_number"] = self.account_number
        datadf["bill_date"] = self.bill_date
        datadf["viewuploaded"] = self.instance
        datadf["entry_type"] = self.entry_type

        cols_to_clean = [
            "surcharges_and_other_charges_and_credits",
            "third_party_charges_includes_tax",
            "taxes_governmental_surcharges_and_fees",
            "monthly_charges",
            "usage_and_purchase_charges",
            "equipment_charges",
            "total_charges"
        ]

        for col in cols_to_clean:
            if col in datadf.columns:
                datadf[col] = datadf[col].astype(str).str.replace("$", "", regex=False)

        model_fields = [f.name for f in UniquePdfDataTable._meta.fields]
        for _, row in datadf.iterrows():
            data = {field: row[field] for field in model_fields if field in row}
            UniquePdfDataTable.objects.create(**data)

        print("Added to unique data table")


    def build_category_object(self, group):
        group['Item Category'] = (group['Item Category'].str.replace(",", "", regex=False).str.replace(" & ", " and ", regex=False).str.upper())
        group['Item Description'] = (group['Item Description'].str.replace(",", "", regex=False).str.replace(" & ", " and ", regex=False).str.upper())
        group['Charges'] = (
            group['Charges']
            .astype(str)                              
            .str.strip()                              
            .replace({"[$,]": ""}, regex=True)       
            .replace("", "0")                       
        )
        group['Charges'] = pd.to_numeric(group['Charges'], errors='coerce').fillna(0)
        summed = (
            group.groupby(['Item Category', 'Item Description'], as_index=False)['Charges']
            .sum()
        )
        result = (
            summed.groupby('Item Category')
            .apply(lambda x: dict(zip(x['Item Description'], x['Charges'])))
            .to_dict()
        )
        return json.dumps(result)

    
    def baseline_data_table(self, datadf):
        baseline_mapping = {
            'Wireless Number': "Wireless_number",
            'Username': "user_name", 
            'Data Usage':"data_usage", 
            'Message Usage':"messaging_usage",
            'Voice Plan Usage':"voice_plan_usage", 
            'Total Charges':"total_charges",
            'Third Party Charges (includes Tax)':"third_party_charges_includes_tax",
            'Taxes, Governmental Surcharges and Fees':"taxes_governmental_surcharges_and_fees",
            "Government fees and taxes": "taxes_governmental_surcharges_and_fees",
            'Surcharges and Other Charges and Credits':"surcharges_and_other_charges_credits", 
            "Company fees and surcharges":"surcharges_and_other_charges_and_credits",
            'Equipment Charges':"equipment_charges",
            'Usage and Purchase Charges':"usage_and_purchase_charges", 
            'Monthly Charges': "monthly_charges",
            "Plans": "plans",
            "Taxes and Surcharges": "taxes_governmental_surcharges_and_fees",
            "Third Party Services":"third_party_charges_includes_tax",
            "Usage Charges": "usage_and_purchase_charges", 
            "Credits & Adjustments": "surcharges_and_other_charges_and_credits",
        }
        
        datadf = datadf.rename(columns=baseline_mapping)
        datadf["company"] = self.company_name
        datadf["sub_company"] = self.sub_company
        datadf["vendor"] = self.vendor_name
        datadf["account_number"] = self.account_number
        datadf["bill_date"] = self.bill_date
        datadf["viewuploaded"] = self.instance

        category_df = datadf.groupby('Wireless_number').apply(
            lambda x: pd.Series({'category_object': self.build_category_object(x)})
        ).reset_index()

        result_df = category_df.merge(datadf.drop_duplicates(subset='Wireless_number'), on="Wireless_number")
        model_fields = [f.name for f in BaselineDataTable._meta.fields]
        for _, row in result_df.iterrows():
            data = {field: row[field] for field in model_fields if field in row}
            BaselineDataTable.objects.create(**data)

        print("Added to baseline data table")

    def make_true_all(self, cat):
        formatted = json.loads(cat) if isinstance(cat, str) else cat
        for key, value in formatted.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict):
                        sub_value['approved'] = True
        return json.dumps(formatted)

    def check_total_under_variance(self,bill_main_id,variance):
        baseline = BaselineDataTable.objects.filter(
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
            account_number=self.account_number,
            viewuploaded=None,
            viewpapered=None
        )
        current_bill = BaselineDataTable.objects.filter(
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
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
    

    def reflect_category_object(self, bill_main_id):
        uniques = UniquePdfDataTable.objects.filter(
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
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
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        uploaded_baseline = UniquePdfDataTable.objects.filter(
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
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
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        uploaded_baseline = BaselineDataTable.objects.filter(
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
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
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
            account_number=self.account_number,
            viewuploaded=None,
            viewpapered=None
        )

        current_bill = BaselineDataTable.objects.filter(
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
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
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
            account_number=self.account_number,
            viewuploaded=bill_main_id
        )
        for line in all_objects:
            line.is_baseline_approved = self.check_true_false(line.category_object)
            line.save()

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
    
    def get_sheet1(self, data):
        basic_data = [data]
        sheet1 = pd.DataFrame(basic_data)
        sheet1["Company"] = self.company_name
        sheet1["Sub Company"] = self.sub_company
        sheet1["Vendor"] = self.vendor_name
        sheet1["Month"] = self.month
        sheet1["Year"] = self.year
        sheet1["Billing Name"] = basic_data[0].get("Billing Info").get("name")
        sheet1["Billing Address"] = basic_data[0].get("Billing Info").get("address")
        sheet1 = sheet1.drop(columns=["Billing Info"])
        sheet1 = sheet1.rename(columns=({"Vendor Url":"Website","Remittance Info":"Remittance Address"}))
        sheet1 = sheet1[["Company", "Sub Company", "Vendor", "Website", "Remittance Address", "Account Number", "Invoice Number", "Bill Date", "Month", "Year", "Total Amount", "Due Date", "Billing Name", "Billing Address"]]

        return sheet1
    
    def get_db_df(self):
        print("def get_db_df")
        db_data = UniquePdfDataTable.objects.filter(
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
            account_number=self.account_number,
            viewuploaded=None,
            viewpapered=None
        )
        if db_data.exists():
            datadf = pd.DataFrame(db_data.values("wireless_number", "cost_center", "User_email", "User_status"))
        else:
            datadf = None
        datadf = datadf.rename(columns={
            "wireless_number": "Wireless Number",
            "cost_center": "Cost Center",
            "User_email": "User_email",
            "User_status": "User_status"
        })
        return datadf
        
    def get_sheet2(self, datadf,dbdf):
        print("def get_sheet2")
        sheet2 = datadf
        sheet2["Account Number"] = self.account_number
        if not "Plans" in sheet2.columns:
            sheet2["Plans"] = "NA"
        
        sheet2 = sheet2.drop(columns=["Page"])
        if dbdf is not None:
            sheet2 = pd.merge(sheet2, dbdf, on="Wireless Number")
        else:
            sheet2["cost_center"] = "NA"
            sheet2["User_email"] = "NA"
            sheet2["User_status"] = "NA"
        # reorder such as put User_email, User_status both immediately after user_name
        cols = sheet2.columns.tolist()
        if "User_email" in cols and "User_status" in cols:
            user_email_index = cols.index("User_email")
            user_status_index = cols.index("User_status")
            user_name_index = cols.index("Username")
            if user_email_index > user_name_index:
                cols.insert(user_name_index + 1, cols.pop(user_email_index))
            if user_status_index > user_name_index + 1:
                cols.insert(user_name_index + 2, cols.pop(user_status_index))

        
        cols.insert(0, cols.pop(cols.index('Account Number')))
        cols.insert(3, cols.pop(cols.index('Plans')))
        sheet2 = sheet2[cols]
        return sheet2
    
    def get_sheet3(self, datadf,dbdf):
        print("def get_sheet3")
        sheet3 = datadf
        sheet3["Account Number"] = self.account_number
        if not "Plans" in sheet3.columns:
            sheet3["Plans"] = "NA"
        sheet3 = sheet3.drop(columns=["Page"])
        if dbdf is not None:
            sheet3 = pd.merge(sheet3, dbdf, on="Wireless Number")
        else:
            sheet3["cost_center"] = "NA"
            sheet3["User_email"] = "NA"
            sheet3["User_status"] = "NA"
        cols = sheet3.columns.tolist()
        # reorder such as put User_email, User_status both immediately after user_name
        if "User_email" in cols and "User_status" in cols:
            user_email_index = cols.index("User_email")
            user_status_index = cols.index("User_status")
            user_name_index = cols.index("Username")
            if user_email_index > user_name_index:
                cols.insert(user_name_index + 1, cols.pop(user_email_index))
            if user_status_index > user_name_index + 1:
                cols.insert(user_name_index + 2, cols.pop(user_status_index))
        
        cols.insert(0, cols.pop(cols.index('Account Number')))
        cols.insert(3, cols.pop(cols.index('Plans')))
        sheet3 = sheet3[cols]
        return sheet3
    
    def get_sheet4(self, datadf,dbdf):
        print("def get_sheet4")
        sheet4 = datadf
        sheet4["Account Number"] = self.account_number
        charges_list = list(sheet4["Total Charges"].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(float))
        sum_of_total_charges = sum(charges_list)
        sheet4["Sum of Total Charges"] = f"{sum_of_total_charges:.2f}"
        if dbdf is not None:
            sheet4 = pd.merge(sheet4, dbdf, on="Wireless Number")
        else:
            sheet4["cost_center"] = "NA"
        sheet4 = sheet4[["Account Number", "Wireless Number", "Username", "Cost Center", "Total Charges", "Sum of Total Charges"]]
        return sheet4
    
    def get_filename(self,path):
        file_path = path.split("/")[-1]        
        name, ext = file_path.rsplit(".", 1)     
        ext = "." + ext                          

        if "_" in name:
            name = name.rsplit("_", 1)[0]

        return f"{name}{ext}"
    
    def parse_bill_date(self, date_str):
        try:
            return parser.parse(date_str, dayfirst=False)  # US-style month/day
        except Exception:
            raise ValueError(f"Date format not supported: {date_str}")

    

    
    def start_process(self):
        if not (self.pdf_path and self.instance and self.company_name and self.sub_company and self.vendor_name):
            return False, "Unable to process pdf due to incomplete data.", None
        try:
            print(self.vendor_name.lower())
            print(self.t_mobile_type)
            if "verizon" in self.vendor_name.lower():
                obj = VerizonClass(self.pdf_path)
            elif 'mobile' in self.vendor_name.lower():
                if self.t_mobile_type == 1:
                    obj = Tmobile1Class(self.pdf_path)
                elif self.t_mobile_type == 2:
                    obj = Tmobile2Class(self.pdf_path)
                else:
                    return False, "Unable to process pdf might be due to t-mobile unsupported format.", 0
            else:
                obj = AttClass(self.pdf_path)
            basic_data, unique_df, baseline_df, ProcessTime = obj.extract_all()
            self.account_number = basic_data.get("Account Number")
            self.net_amount = basic_data.get("Total Amount")
            self.bill_date = basic_data.get("Bill Date")
            onboarded = BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).filter(sub_company=self.sub_company, vendor=self.vendor_name, accountnumber=self.account_number).first()
            onboarded_id = onboarded.banOnboarded
            baseinstance = self.base_data_table(basic_data)
            print(onboarded.variance)
            baseinstance.variance = onboarded.variance
            baseinstance.save()
            bill_main_id = baseinstance.viewuploaded.id
            self.pdf_data_table(baseline_df)
            self.unique_data_table(unique_df)
            self.baseline_data_table(baseline_df)


            self.reflect_category_object(bill_main_id)
            self.reflect_baselinetable_non_bill_data(bill_main_id=bill_main_id, onboarded_id=onboarded_id)
            self.reflect_uniquetable_non_bill_data(bill_main_id=bill_main_id, onboarded_id=onboarded_id)
            
            self.add_tag_to_dict(bill_main_id, onboarded.variance)
            self.check_total_under_variance(bill_main_id=bill_main_id, variance=onboarded.variance)
            self.check_baseline_approved(UniquePdfDataTable, bill_main_id)
            self.check_baseline_approved(BaselineDataTable, bill_main_id)

            account_obj = BaselineDataTable.objects.filter(sub_company=self.sub_company, vendor=self.vendor_name, account_number=self.account_number).filter(viewuploaded=self.instance)
            approved_wireless_list = account_obj.values_list('is_baseline_approved', flat=True)

            is_approved = False if False in list(approved_wireless_list) else True
            baseinstance.is_baseline_approved = is_approved
            baseinstance.bill_approved_date = timezone.now()
            baseinstance.save()
            
            db_df = self.get_db_df()
            workbook = self.dataframe_to_excel(self.get_sheet1(basic_data), self.get_sheet2(unique_df,db_df), self.get_sheet3(baseline_df,db_df), self.get_sheet4(unique_df,db_df))
            workbook_name = str(self.pdf_filename).split("/")[-1].replace(".pdf", ".xlsx")
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
                    vendor_name=self.vendor_name,
                    company_name=self.company_name,
                    sub_company_name=self.sub_company,
                    workbook_name=workbook_name,
                    bill_date_info=self.bill_date
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

                message = 'PDF uploaded successfully'
            except Exception as e:
                print(e)
                message = str(e).strip()
            print("Process completed successfully.")
            create_notification(user=self.user_obj, msg=f"Bill with date {self.bill_date} of ban {self.account_number} uploaded.",company=self.company_obj)
            return True, message, ProcessTime
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            if self.instance and self.instance.pk: self.instance.delete()
            return False, str(e), 0
    