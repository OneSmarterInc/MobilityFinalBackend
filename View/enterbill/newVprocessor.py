from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable, BaselineDataTable, PdfDataTable, PortalInformation
import logging
import pdfplumber
from Scripts.VerizonNew import VerizonClass
import pandas as pd
import io
import json
import os
from django.conf import settings
from ..models import ProcessedWorkbook
from django.core.files import File
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class ProcessPdf2:
    def __init__(self, buffer_data,instance=None):
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
        self.types = self.buffer_data.get('types')
        self.email = self.buffer_data.get('email')
        self.sub_company = self.buffer_data.get('sub_company_name')
        self.t_mobile_type = self.check_tmobile_type() if 'mobile' in str(self.vendor_name).lower() else 0

        logger.info(f'Processing PDF from buffer: {self.pdf_path}, {self.company_name}, {self.vendor_name}, {self.pdf_filename}')

        self.bill_date = None
        self.net_amount = 0
        self.check = True
        self.account_number = None

    def check_tmobile_type(self):
        print("def check_tmobile_type")
        Lines = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                if i == 0:
                    page_text = page.extract_text()
                    lines = page_text.split('\n')
                    Lines.extend(lines)
                else:
                    break

        if 'Bill period Account Invoice Page' in Lines[0]:
            print("Type2 : Bill period Account Invoice Page")
            return 2
        elif 'Your Statement' in Lines[0]:
            print("Type1 : Your Statement")
            return 1
        else:
            return 0
        
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
        return BaseDataTable.objects.create(**baseDatamapped)
        
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
            'Surcharges and Other Charges and Credits':"surcharges_and_other_charges_credits", 
            'Equipment Charges':"equipment_charges",
            'Usage and Purchase Charges':"usage_and_purchase_charges", 
            'Monthly Charges': "monthly_charges",
            "Item Category": "item_category",
            "Item Description": "item_description",
            "Charges": "item_charges",
            "Plans": "plans",
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
            'Surcharges and Other Charges and Credits':"surcharges_and_other_charges_credits", 
            'Equipment Charges':"equipment_charges",
            'Usage and Purchase Charges':"usage_and_purchase_charges", 
            'Monthly Charges': "monthly_charges",
            "Plans": "plans",
        }
        datadf = datadf.rename(columns=unique_mapping)
        datadf["company"] = self.company_name
        datadf["sub_company"] = self.sub_company
        datadf["vendor"] = self.vendor_name
        datadf["account_number"] = self.account_number
        datadf["bill_date"] = self.bill_date
        datadf["viewuploaded"] = self.instance
        datadf["entry_type"] = self.entry_type

        model_fields = [f.name for f in UniquePdfDataTable._meta.fields]
        for _, row in datadf.iterrows():
            data = {field: row[field] for field in model_fields if field in row}
            UniquePdfDataTable.objects.create(**data)

        print("Added to unique data table")


    def build_category_object(self, group):
        return json.dumps(group.groupby('Item Category').apply(
            lambda x: dict(zip(x['Item Description'], x['Charges'].replace("$","").replace(",","")))
        ).to_dict())
    
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
            'Surcharges and Other Charges and Credits':"surcharges_and_other_charges_and_credits", 
            'Equipment Charges':"equipment_charges",
            'Usage and Purchase Charges':"usage_and_purchase_charges", 
            'Monthly Charges': "monthly_charges",
            "Plans": "plans",
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

    def add_tag_to_dict(self, bill_main_id):
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
                tagged_object = tagging(baseline_obj.category_object, bill_obj.category_object)
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
        return datadf
        
    def get_sheet2(self, datadf,dbdf):
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
        sheet4 = datadf
        sheet4["Account Number"] = self.account_number
        charges_list = list(sheet4["Total Charges"].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(float))
        sum_of_total_charges = sum(charges_list)
        sheet4["Sum of Total Charges"] = f"{sum_of_total_charges:.2f}"
        if dbdf is not None:
            sheet4 = pd.merge(sheet4, dbdf, on="Wireless Number")
        else:
            sheet4["cost_center"] = "NA"
        sheet4 = sheet4[["Account Number", "Wireless Number", "Username", "cost_center", "Total Charges", "Sum of Total Charges"]]
        return sheet4
    
    def start_process(self):
        if not (self.pdf_path and self.instance and self.company_name and self.sub_company and self.vendor_name):
            return False, "Unable to process pdf due to incomplete data.", None
        try:
            obj = VerizonClass(self.pdf_path)
            basic_data, unique_df, baseline_df, ProcessTime = obj.extract_all()
            self.account_number = basic_data.get("Account Number")
            self.net_amount = basic_data.get("Total Amount")
            self.bill_date = basic_data.get("Bill Date")
            onboarded = BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).filter(sub_company=self.sub_company, vendor=self.vendor_name, accountnumber=self.account_number).first()
            onboarded_id = onboarded.banOnboarded
            baseinstance = self.base_data_table(basic_data)
            bill_main_id = baseinstance.viewuploaded.id
            self.pdf_data_table(baseline_df)
            self.unique_data_table(unique_df)
            self.baseline_data_table(baseline_df)

            self.reflect_uniquetable_non_bill_data(bill_main_id=bill_main_id, onboarded_id=onboarded_id)
            self.reflect_baselinetable_non_bill_data(bill_main_id=bill_main_id, onboarded_id=onboarded_id)
            self.add_tag_to_dict(bill_main_id)
            self.reflect_category_object(bill_main_id)
            self.check_baseline_approved(UniquePdfDataTable, bill_main_id)
            self.check_baseline_approved(BaselineDataTable, bill_main_id)

            account_obj = BaselineDataTable.objects.filter(sub_company=self.sub_company, vendor=self.vendor_name, account_number=self.account_number).filter(viewuploaded=self.instance)
            approved_wireless_list = account_obj.values_list('is_baseline_approved', flat=True)

            baseinstance.is_baseline_approved = False if False in list(approved_wireless_list) else True
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
            return True, message, ProcessTime
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return False, str(e), 0
        
from addon import parse_until_dict, get_close_match_key
def tagging(baseline_data, bill_data):
    baseline_data = parse_until_dict(baseline_data)
    bill_data = parse_until_dict(bill_data)
    def compare_and_tag(base, bill):
        for key in list(bill.keys()):
            closely_matched = get_close_match_key(key,list(base.keys()))
            if not closely_matched:
                print("not closely matched!")
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