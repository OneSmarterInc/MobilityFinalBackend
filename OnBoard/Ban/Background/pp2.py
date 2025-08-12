from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable, BaselineDataTable, PdfDataTable, PortalInformation
import logging
import pdfplumber
from Scripts.VerizonNew import VerizonClass
import pandas as pd
import json
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
        self.email = self.buffer_data.get('user_email')
        self.sub_company = self.buffer_data.get('sub_company')
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
            "banOnboarded": self.instance,
            "sub_company": self.sub_company,
            "vendor": self.vendor_name,
            "company": self.company_name,
            "location": self.location,
            "master_account": self.master_account,
            "Entry_type":self.entry_type,
        }
        BaseDataTable.objects.create(**baseDatamapped)
        
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
            "Plans":"plans"

        }
        datadf = datadf.rename(columns=pdf_mapping)
        datadf["company"] = self.company_name
        datadf["sub_company"] = self.sub_company
        datadf["vendor"] = self.vendor_name
        datadf["account_number"] = self.account_number
        datadf["bill_date"] = self.bill_date
        datadf["banOnboarded"] = self.instance
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
        datadf["banOnboarded"] = self.instance
        datadf["entry_type"] = self.entry_type

        model_fields = [f.name for f in UniquePdfDataTable._meta.fields]
        for _, row in datadf.iterrows():
            data = {field: row[field] for field in model_fields if field in row}
            UniquePdfDataTable.objects.create(**data)

        print("Added to unique data table")


    def build_category_object(self, group):
        group['Item Category'] = group['Item Category'].str.upper()
        group['Item Description'] = group['Item Description'].str.upper()

        return json.dumps(
            group.groupby('Item Category').apply(
                lambda x: dict(
                    zip(
                        x['Item Description'],
                        x['Charges'].replace({"$": "", ",": ""}, regex=True)
                    )
                )
            ).to_dict()
        )

    
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
        datadf["banOnboarded"] = self.instance

        category_df = datadf.groupby('Wireless_number').apply(
            lambda x: pd.Series({'category_object': self.build_category_object(x) if self.baseline_check else {}})
        ).reset_index()

        result_df = category_df.merge(datadf.drop_duplicates(subset='Wireless_number'), on="Wireless_number")
        model_fields = [f.name for f in BaselineDataTable._meta.fields]
        for _, row in result_df.iterrows():
            data = {field: row[field] for field in model_fields if field in row}
            BaselineDataTable.objects.create(**data)

        print("Added to baseline data table")

    
    def portal_information(self, data):
        portal_mapping = {
            "URL": data.get("Vendor Url"),
            "Customer_Name":self.sub_company,
            "Account_number": self.account_number,
            "User_email_id":self.email,
            "banOnboarded":self.instance
        }
        PortalInformation.objects.create(**portal_mapping)

        print("Added to portal information table")

    def reflect_category_object(self):
        uniques = UniquePdfDataTable.objects.filter(
            company=self.company_name,
            sub_company=self.sub_company,
            vendor=self.vendor_name,
            account_number=self.account_number
        )

        for line in uniques:
            baseline = BaselineDataTable.objects.filter(
                company=line.company,
                sub_company=line.sub_company,
                vendor=line.vendor,
                account_number=self.account_number,
                Wireless_number=line.wireless_number
            ).first()

            if baseline:
                line.category_object = baseline.category_object
                line.save()
    def start_process(self):
        if not (self.pdf_path and self.instance and self.company_name and self.sub_company and self.vendor_name):
            return False, "Unable to process pdf due to incomplete data.", None
        try:
            obj = VerizonClass(self.pdf_path)
            basic_data, unique_df, baseline_df, ProcessTime = obj.extract_all()
            self.account_number = basic_data.get("Account Number")
            self.net_amount = basic_data.get("Total Amount")
            self.bill_date = basic_data.get("Bill Date")
            self.base_data_table(basic_data)
            if not "master" in self.entry_type.lower():
                self.portal_information(basic_data)
                self.pdf_data_table(baseline_df)
                self.unique_data_table(unique_df)
                if not "master" in self.entry_type.lower():
                    self.baseline_data_table(baseline_df)
                self.reflect_category_object()
            print("Process completed successfully.")
            return True, "PDF Onboarded successfully", ProcessTime
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return False, str(e), 0
        