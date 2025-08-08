import sqlite3
import json,re
from pathlib import Path
import time,os,zipfile
import pandas as pd
from io import BytesIO,StringIO
from Scripts.verizon import PDFExtractor, First, Model1, Model2, Model3, Model4
from Scripts.Att import first_page_extractor, Att, process_all
from Scripts.tmobile1 import get_all_dataframes_type_1
from Scripts.tmobile2 import extract_text_from_t_mobile_2
batch_count = '000'
from datetime import datetime
from collections import defaultdict
import logging
import smtplib
from email.mime.text import MIMEText
import numpy as np
import pdfplumber
from ..models import UniquePdfDataTable
import ast
from django.db import transaction
from ..models import BaseDataTable
from ..models import PdfDataTable
from django.db.models import Max
from django.db import transaction
from ..models import BatchReport, PortalInformation
from django.db import models
from ..models import BaselineDataTable
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from sendmail import send_custom_email

class ProcessPdf:
    def __init__(self, buffer_data,instance):
        self.buffer_data = buffer_data
        self.pdf_path = self.buffer_data['pdf_path'] if 'pdf_path' in self.buffer_data else None
        self.company_name = self.buffer_data['company_name'] if 'company_name' in self.buffer_data else None
        self.vendor_name = self.buffer_data['vendor_name'] if 'vendor_name' in self.buffer_data else None
        self.pdf_filename = self.buffer_data['pdf_filename'] if 'pdf_filename' in self.buffer_data else None
        self.month = self.buffer_data['month'] if 'month' in self.buffer_data else None
        self.entry_type = self.buffer_data['entry_type'] if 'entry_type' in self.buffer_data else None
        self.baseline_check = True if self.buffer_data['baseline_check'] in ('true',True,'True') else False
        self.location = self.buffer_data['location'] if 'location' in self.buffer_data else None
        self.master_account = self.buffer_data['master_account'] if 'master_account' in self.buffer_data else None
        self.year = self.buffer_data['year'] if 'year' in self.buffer_data else None
        self.types = self.buffer_data['types'] if 'types' in self.buffer_data else None
        self.email = self.buffer_data['user_email'] if 'user_email' in self.buffer_data else None
        self.sub_company = self.buffer_data['sub_company'] if 'sub_company' in self.buffer_data else None
        self.t_mobile_type = self.check_tmobile_type() if 'mobile' in str(self.vendor_name).lower() else 0
        logger.info(f'Processing PDF from buffer: {self.pdf_path}, {self.company_name}, {self.vendor_name}, {self.pdf_filename}')

        self.bill_date = None

        self.instance = instance
        self.net_amount = 0
        self.check = True

        self.account_number = None
        self.billing_address = {}
    
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
    def extract_data_from_pdf(self):
        print("def extract_data_from_pdf")
        logger.info(f'Extracting data from PDF: {self.pdf_path}')

        if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
            base_data_df,pdf_df,temp,rox,on,dates,acc_nos = get_all_dataframes_type_1(self.pdf_path)
            if isinstance(base_data_df, pd.DataFrame):
                base_data_df.drop(columns=['Previous Balance','Grand Total','Monthly Recurring Charges','Other Charges', 'Taxes & Surcharges'],inplace=True)
                base_data_df.rename(columns={'Account Number':'AccountNumber','Address':"Billing Address",'Vendor_Address':'Remidence_Address'},inplace=True)
                base_data_df.columns = base_data_df.columns.str.replace(' ', '_')
            data_dict = base_data_df.to_dict(orient='records')
            acc_info = acc_nos
            bill_date_info = dates
            data_dict = data_dict[0]
            data_dict['company'] = self.company_name
            data_dict['vendor'] = self.vendor_name
            data_dict['pdf_path'] = self.pdf_path
            data_dict['pdf_filename'] = self.pdf_filename
            data_dict['month'] = self.month
            data_dict['year'] = self.year
            data_dict['sub_company'] = self.sub_company
            data_dict['Bill_Date'] = dates
            data_dict['entry_type'] = self.entry_type

            data_dict['location'] = self.location
            data_dict['master_account'] = self.master_account

        elif 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 2:
            unique_df,base_df,temp_check = extract_text_from_t_mobile_2(self.pdf_path)
            base_df.rename(columns={'account.number':'AccountNumber','invoice.number':'InvoiceNumber'},inplace=True)
            data_dict = base_df.to_dict(orient='records')
            acc_info = '12345678'
            bill_date_info = 'jan1'
            data_dict = data_dict[0]
            data_dict['company'] = self.company_name
            data_dict['vendor'] = self.vendor_name
            data_dict['pdf_path'] = self.pdf_path
            data_dict['pdf_filename'] = self.pdf_filename
            data_dict['month'] = self.month
            data_dict['year'] = self.year
            data_dict['sub_company'] = self.sub_company  
        elif 'verizon' in str(self.vendor_name).lower():
            lines_to_extract = [2, 3, 4, 5]
            extractor = PDFExtractor(self.pdf_path)
            extractor.extract_data()
            extractor.process_pdf(lines_to_extract)
            data = extractor.get_result_df()
            acc_info = extractor.get_accounts_info()
            bill_date_info = extractor.get_bill_date()
            self.net_amount = extractor.get_net_amount()
            self.billing_address = extractor.get_billing_address()
            data_dict = data.to_dict(orient='records')
            for entry in data_dict:
                entry['company'] = self.company_name
                entry['vendor'] = self.vendor_name
                entry['pdf_path'] = self.pdf_path
                entry['pdf_filename'] = self.pdf_filename
                entry['month'] = self.month
                entry['year'] = self.year
                entry['sub_company'] = self.sub_company
                entry['entry_type'] = self.entry_type

                entry['location'] = self.location
                entry['master_account'] = self.master_account
        else:
        # elif vendor_nm in at_vendor_list:
            first_obj = first_page_extractor(self.pdf_path)
            data_dict = first_obj.first_page_data_func()
            acc_info = first_obj.get_acc_info()
            bill_date_info = first_obj.get_bill_date_info()
            self.billing_address = first_obj.get_billing_info()
            
            data_dict['company'] = self.company_name
            data_dict['vendor'] = self.vendor_name
            data_dict['pdf_path'] = self.pdf_path
            data_dict['pdf_filename'] = self.pdf_filename
            data_dict['month'] = self.month
            data_dict['year'] = self.year
            data_dict['sub_company'] = self.sub_company
            data_dict['entry_type'] = self.entry_type
            self.net_amount = first_obj.get_net_amount()
            data_dict['location'] = self.location
            data_dict['master_account'] = self.master_account

        return data_dict,acc_info,bill_date_info
    def save_to_base_data_table(self, data):
    
        print("def save_to_base_data_table")
        
        mapping = {"Date_Due":"date_due", "AccountNumber":"accountnumber","InvoiceNumber":"invoicenumber", "Website":"website","Duration":"duration","Bill_Date":"bill_date","Client_Address":"RemittanceAdd","entry_type":"Entry_type","Remidence_Address":"RemittanceAdd"}
        print("billing==",self.billing_address)
        billing = {
            "BillingName" : self.billing_address["name"] if "name" in self.billing_address else None,
            "BillingAdd": self.billing_address["address"] if "address" in self.billing_address else None,
            "BillingAtn" : self.billing_address["attn"] if "attn" in self.billing_address else None,
        }
        if type(data) == dict:
            updated_data = {mapping.get(k, k): v for k, v in data.items()}
            updated_data.pop("foundation_account") if 'foundation_account' in updated_data else None
            filtered_data = remove_filds(BaseDataTable, updated_data)
            filtered_data['location'] = self.location
            bill_date = filtered_data.pop('bill_date').replace(',','')
            self.bill_date = bill_date
            obj = BaseDataTable.objects.create(banOnboarded=self.instance, bill_date=bill_date, net_amount=self.net_amount,**billing, **filtered_data)
            self.account_number = obj.accountnumber
        elif type(data) == list:
            for item in data:
                updated_data = {mapping.get(k, k): v for k, v in item.items()}
                updated_data.pop("foundation_account") if 'foundation_account' in updated_data else None
                filtered_data = remove_filds(BaseDataTable, updated_data)
                bill_date = filtered_data.pop('bill_date').replace(',','')
                self.bill_date = bill_date
                obj = BaseDataTable.objects.create(banOnboarded=self.instance, bill_date=bill_date, net_amount=self.net_amount,**billing, **filtered_data)
                self.account_number = obj.accountnumber

    def save_to_portal_info(self, data):
        obj = PortalInformation.objects.create(
            URL = data['Website'] if 'Website' in data else None,
            banOnboarded = self.instance,
            Customer_Name = self.sub_company,
            Vendor = self.vendor_name,
            Account_number = data['AccountNumber'],
            User_email_id = self.email,
        )
        obj.save()
    def extract_total_pdf_data(self,acc_info,bill_date):
        print("def extract_total_pdf_data")
        total_dict = None
        result_df = None
        tmp_df = None
        if 'mobile' in str(self.vendor_name).lower():
            print("vendor name is mobile")
            if self.t_mobile_type == 1:
                print('got first')
                print('>>>>>>>>>>>>><<<<<<<<<<<<<<>>>>>>>>>>>>><<<<<<<<<<<>>>>>>>>>>>')
                base_data_df,pdf_df,tmp_df,in_valid_df,usage_df,dates,acc_nos = get_all_dataframes_type_1(self.pdf_path)
                print('>>>>>>>>>>>>>>>qwertyui<<<<<<<<<<<<')
                pdf_df['account_number'] = acc_info
                total_dict = pdf_df.to_dict(orient='records')
                result_df = pdf_df
            elif self.t_mobile_type == 2:
                print('got second')
                unique_df,base_data_df,detail_df = extract_text_from_t_mobile_2(self.pdf_path)
                total_dict = unique_df.to_dict(orient='records')
                result_df = unique_df
            else:
                return {'message': 'Invalid tmobile type', 'Error' : 1}
        elif 'verizon' in str(self.vendor_name).lower():
            extractor = Model4(self.pdf_path,acc_info)
            result,tmp_df = extractor.process_pdf()
            temp_result_df = result
            df_unique = temp_result_df.drop_duplicates(subset=['Wireless_number'])
            df_unique_dict = df_unique.to_dict(orient='records')
            total_dict = df_unique_dict
            result_df = result
        else:
            df_unique,final_df,usage_df,tmp_df = process_all(self.pdf_path)
            # edit all wireless_numbers from Wireless number column from df_unique
            df_unique['Wireless_number'] = df_unique['Wireless_number'].astype(str).str.replace('.', '-', regex=False)
            final_df['Wireless_number'] = final_df['Wireless_number'].astype(str).str.replace('.', '-', regex=False)
            tmp_df['Wireless_number'] = tmp_df['Wireless_number'].astype(str).str.replace('.', '-', regex=False)
            # print("df unique=\n",df_unique)
            # print("final df=\n",final_df.columns)
            # print("tmp df=\n",tmp_df.columns)
            df_unique['account_number'] = acc_info
            final_df['account_number'] = acc_info
            df_unique_dict = df_unique.to_dict(orient='records')
            total_dict = df_unique_dict
            result_df = final_df
        for entry in total_dict:
            entry['company'] = self.company_name
            entry['vendor'] = self.vendor_name
            entry['sub_company'] = self.sub_company

            entry['location'] = self.location

            if isinstance(bill_date, list):
                entry['bill_date'] = bill_date[0]
            else:
                entry['bill_date'] = bill_date
        res_data_dict = result_df.to_dict(orient='records')
        for entry in res_data_dict:
            entry['company'] = self.company_name
            entry['vendor'] = self.vendor_name
            entry['sub_company'] = self.sub_company
            entry['location'] = self.location
        return res_data_dict,total_dict,tmp_df
    def save_to_pdf_data_table(self, data):
        
        print('saving to pdf data table')
        data_df = pd.DataFrame(data)
        print('in saves B')
        if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
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
            # Rename columns in the DataFrame according to the mapping and drop the rest
            data_df = data_df.rename(columns=column_mapping)
            data_df = data_df[[col for col in data_df.columns if col in column_mapping.values()]]
        elif 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 2:
            # Create a dictionary to map old column names to new model field names
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

                # Drop columns not in the mapping
                df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

                # Rename the columns based on the mapping
                data_df = df_filtered.rename(columns=column_mapping)

        if 'Page Number' in data_df.columns:
            columns_to_drop = ['Page Number', 'Monthly charges Add-ons', 'Billing_Name', 
                            'Billing_Address', 'Remidence_Addresss', 'Activity since last bill']

            # Drop only the columns that exist in the DataFrame
            data_df.drop(columns=[col for col in columns_to_drop if col in data_df.columns], inplace=True)

        data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account_number':'Account_number','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data_df.columns = data_df.columns.str.replace('&', 'and')
        data_df.columns = data_df.columns.str.replace('-', ' ')
        data_df.columns = data_df.columns.str.replace(' ', '_')
        data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data = data_df.to_dict(orient='records')
        
        mapping = {'Wireless_number':"wireless_number", 'Monthly_Charges':"monthly_charges", 'Usage_and_Purchase_Charges':"usage_and_purchase_charges", 'Equipment_Charges':"equipment_charges", 'Surcharges_and_Other_Charges_and_Credits':"surcharges_and_other_charges_and_credits", 'Taxes_Governmental_Surcharges_and_Fees':"taxes_governmental_surcharges_and_fees", 'Third_Party_Charges_includes_Tax':"taxes_governmental_surcharges_and_fees", 'Total_Charges':"total_charges", 'Voice_Plan_Usage':"voice_plan_usage", 'Messaging_Usage':"messaging_usage", 'Data_Usage':"data_usage", 'Foundation_Account':"voice_plan_usage", 'Account_number':"account_number", 'Group_Number':"group_number", 'User_Email':"user_email", 'Status':"status", 'Cost_Center':"cost_center", 'Account_Charges_and_Credits':"account_charges_credits", 'Plans':"plans", 'Item_Category':"item_category", 'Item_Description':"item_description", 'Charges':"charges","User_name":"user_name"}
        

        for item in data:
            item.pop('Note') if 'Note' in item else None
            item.pop('foundation_account') if 'foundation_account' in item else None
            updated_data = {mapping.get(k, k): v for k, v in item.items()}
            filtered_data = remove_filds(PdfDataTable, updated_data)
            PdfDataTable.objects.create(banOnboarded=self.instance, **filtered_data)
            
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
    def save_to_batch_report(self, data, vendor):
        try:
            if 'mobile' in str(self.vendor_name).lower():
                return None
            # if vendor in ['T_Mobile','t-mobile','T-mobile','t_mobile']:
            #     return None
            if 'verizon' in str(self.vendor_name).lower():
                temp = data[0]
                temp_fig = data[0]
            else:
                temp = data
                temp_fig = data
                

            bill_date = temp['Bill_Date']
            try:
                date_object = datetime.strptime(bill_date, '%B %d %Y')
                formatted_date = date_object.strftime('%m/%d/%Y')
                temp_fig["Bill_Date"] = formatted_date
            except:
                try:
                    date_obj = datetime.strptime(bill_date, '%b %d, %Y')
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    temp_fig["Bill_Date"] = formatted_date
                except:
                    temp_fig['Bill_Date'] = 'NA'

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
            at_vendor_list = ['AT&T', 'AT n T', 'ATT', 'at&t', 'att', 'at n t']
            if str(self.vendor_name).lower().startswith('a') and str(self.vendor_name).lower().endswith('t'):
                temp = data
                temp_fig = data
            else:
                temp = data
                temp_fig = data

            bill_date = temp['bill_date']
            try:
                date_object = datetime.strptime(bill_date, '%B %d %Y')
                formatted_date = date_object.strftime('%m/%d/%Y')
                temp_fig['Bill_Date'] = temp_fig.pop('bill_date')
                temp_fig["Bill_Date"] = formatted_date
            except:
                try:
                    date_obj = datetime.strptime(bill_date, '%b %d, %Y')
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    temp_fig['Bill_Date'] = temp_fig.pop('bill_date')
                    temp_fig["Bill_Date"] = formatted_date
                except:
                    temp_fig['Bill_Date'] = temp_fig.pop('bill_date')
                    temp_fig['Bill_Date'] = 'NA'

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
            'Bill_Date': 'Invoice_Date',
            'Remidence_Address': 'Vendor_Address_1',
            'Billing_Name': 'Cust_Id',
            'Total_Charges': 'Net_Amount',
            'vendor': 'Vendor_Name_1',
            'company_name': 'company',
            'Vendor_City': 'Vendor_City',
            'Vendor_State': 'Vendor_State',
            'Vendor_Zip': 'Vendor_Zip',
            'entry_type':'Entry_type',
            'NetAmount':'Net_Amount'
        }

        fields_to_remove = [
            'Website',
            'Duration',
            'pdf_path',
            'pdf_filename',
            'Billing_Address',
            'Client_Address',
            'foundation_account'
        ]

        for field in fields_to_remove:
            if field in temp_fig:
                del temp_fig[field]

        renamed_data = {key_mapping.get(key, key): value for key, value in temp_fig.items()}

        with transaction.atomic():
            # Step 1: Check if record exists
            existing_data = BatchReport.objects.filter(
                Customer_Vendor_Account_Number=renamed_data['Customer_Vendor_Account_Number'],
                company=renamed_data['company'],
                Vendor_Name_1=renamed_data['Vendor_Name_1'],
                Invoice_Date=renamed_data['Invoice_Date']
            ).first()

            # Step 2: Determine Vendor Short Name
            batch_vendor = self.vendor_name
            if str(self.vendor_name).lower().startswith('a') and str(self.vendor_name).lower().endswith('t'):
                batch_vendor = 'ATT'
            elif str(self.vendor_name).lower().startswith('v') and str(self.vendor_name).lower().endswith('n'):
                batch_vendor = 'VER'

            # Step 3: Vendor location info
            entered_vendor_zip = zip_code
            entered_vendor_state = state
            entered_vendor_city = city

            # Step 4: Check location match
            location_qs = BatchReport.objects.filter(
                Vendor_Zip=entered_vendor_zip,
                Vendor_State=entered_vendor_state,
                Vendor_City=entered_vendor_city
            )

            if location_qs.exists():
                # Step 5: Get max Location_Code
                max_code = (
                    location_qs
                    .annotate(code_num=models.functions.Substr('Location_Code', 4))
                    .aggregate(max_code=Max('code_num'))['max_code']
                )

                if max_code and max_code.isdigit():
                    new_location_code = f"{batch_vendor}{str(int(max_code) + 1).zfill(3)}"
                else:
                    new_location_code = f"{batch_vendor}001"

                # Step 6: Update all matching location rows
                location_qs.update(Location_Code=new_location_code)
                print("Location code assigned/updated:", new_location_code)
            else:
                print("The entered vendor-zip does not exist in the database.")
                new_location_code = None

            # Step 7: Update or insert
            if existing_data:
                existing_data.Due_Date = renamed_data['Due_Date']
                existing_data.Invoice_Number = renamed_data['Invoice_Number']
                existing_data.Invoice_Date = renamed_data['Invoice_Date']
                existing_data.Cust_Id = renamed_data['Cust_Id']
                existing_data.Net_Amount = renamed_data['Net_Amount']
                existing_data.save()
            else:
                record = BatchReport.objects.create(**renamed_data,banOnboarded=self.instance)

                # Optional: Assign location code after insert
                if new_location_code:
                    BatchReport.objects.filter(
                        Vendor_Zip=entered_vendor_zip,
                        Vendor_State=entered_vendor_state,
                        Vendor_City=entered_vendor_city
                    ).update(Location_Code=new_location_code)
    def save_to_unique_pdf_data_table(self,data):
        print("saving to unique_pdf_data_table")
        data_df = pd.DataFrame(data)

        
        if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
        # if vendor in ['T_Mobile','t-mobile','T-mobile','t_mobile'] and types== 'first':
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

            # Drop any columns not in the mapping
            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            # Rename the columns
            data_df = df_filtered.rename(columns=column_mapping)
        elif 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 2:
        # elif vendor in ['T_Mobile','t-mobile','T-mobile','t_mobile'] and types== 'second':
            # Create a dictionary to map old column names to new model field names
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
            columns_to_drop = ['Page Number', 'Monthly charges Add-ons', 'Billing_Name', 
                            'Billing_Address', 'Remidence_Addresss', 'Activity since last bill']

            # Drop only the columns that exist in the DataFrame
            data_df.drop(columns=[col for col in columns_to_drop if col in data_df.columns], inplace=True)

        data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account Number':'account_number_y','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data_df.columns = data_df.columns.str.replace('&', 'and')
        data_df.columns = data_df.columns.str.replace('-', ' ')
        data_df.columns = data_df.columns.str.replace(' ', '_')
        data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data = data_df.to_dict(orient='records')
        mapping = {'Wireless_number':"wireless_number", 'Monthly_charges':"monthly_charges", 'Usage_and_Purchase_Charges':"usage_and_purchase_charges", 'Equipment_Charges':"equipment_charges", 'surcharges_and_other_charges_and_credits':"surcharges_and_other_charges_credits", 'Taxes_Governmental_Surcharges_and_Fees':"taxes_governmental_surcharges_and_fees", 'Third_Party_Charges_includes_Tax':"taxes_governmental_surcharges_and_fees", 'Total_Charges':"total_charges", 'Voice_Plan_Usage':"voice_plan_usage", 'Messaging_Usage':"messaging_usage", 'Data_Usage':"data_usage", 'Foundation_Account':"voice_plan_usage", 'Account_number':"account_number", 'Group_Number':"group_number", 'User_Email':"User_email", 'Status':"User_status", 'Cost_Center':"cost_center", 'Account_Charges_and_Credits':"account_charges_and_credits", 'Plans':"plans", 'Item_Category':"item_category", 'Item_Description':"item_description", 'Charges':"charges", "User_name":"user_name", "Monthly_Charges":"monthly_charges","Surcharges_and_Other_Charges_and_Credits":'surcharges_and_other_charges_credits'}

        for item in data:
            updated_data = {mapping.get(k, k): v for k, v in item.items()}
            updated_data.pop('charges') if 'charges' in updated_data else None
            updated_data.pop('location') if 'location' in updated_data else None
            updated_data.pop('Note') if 'Note' in updated_data else None
            updated_data.pop('foundation_account') if 'foundation_account' in item else None
            updated_data.pop('bill_date') if 'bill_date' in item else None
            filtered_data = remove_filds(UniquePdfDataTable, updated_data)
            UniquePdfDataTable.objects.create(banOnboarded=self.instance,bill_date=self.bill_date,**filtered_data)
    def save_to_baseline_data_table(self,data):
        print("saving to baseline_data_table")
        data_df = pd.DataFrame(data)
        if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
            column_mapping = {
                'Wireless_number': 'Wireless_number',
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
        elif 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 2:
            # Create a dictionary to map old column names to new model field names
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
            columns_to_drop = ['Page Number', 'Monthly charges Add-ons', 'Billing_Name', 
                            'Billing_Address', 'Remidence_Addresss', 'Activity since last bill']

            data_df.drop(columns=[col for col in columns_to_drop if col in data_df.columns], inplace=True)

        data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account Number':'account_number_y','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data_df.columns = data_df.columns.str.replace('&', 'and')
        data_df.columns = data_df.columns.str.replace('-', ' ')
        data_df.columns = data_df.columns.str.replace(' ', '_')
        data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data = data_df.to_dict(orient='records')
     
        
        mapping = {'Monthly_charges':"monthly_charges", 'Usage_and_Purchase_Charges':"usage_and_purchase_charges", 'Equipment_Charges':"equipment_charges", 'Taxes_Governmental_Surcharges_and_Fees':"taxes_governmental_surcharges_and_fees", "Surcharges_and_Other_Charges_and_Credits":"surcharges_and_other_charges_and_credits",
        'Third_Party_Charges_includes_Tax':"taxes_governmental_surcharges_and_fees", 'Total_Charges':"total_charges", 'Voice_Plan_Usage':"voice_plan_usage", 'Messaging_Usage':"messaging_usage", 'Data_Usage':"data_usage", 'Foundation_Account':"voice_plan_usage", 'Account_number':"account_number", 'Group_Number':"group_number", 'User_Email':"User_email", 'Status':"User_status", 'Cost_Center':"cost_center", 'Account_Charges_and_Credits':"account_charges_and_credits", 'Plans':"plans", 'Item_Category':"item_category", 'Item_Description':"item_description", 'Charges':"charges", "User_name":"user_name", "Monthly_Charges":"monthly_charges"}
        for item in data:
            for key, value in item.items():
                if isinstance(value, dict):
                    item[key] = json.dumps(value)  
            updated_data = {mapping.get(k, k): v for k, v in item.items()}
            updated_data.pop('group_number') if 'group_number' in updated_data else None
            updated_data.pop('location') if 'location' in updated_data else None
            updated_data.pop('User_email') if 'User_email' in updated_data else None
            updated_data.pop('User_status') if 'User_status' in updated_data else None
            updated_data.pop('item_category') if 'item_category' in updated_data else None
            updated_data.pop('item_description') if 'item_description' in updated_data else None
            updated_data.pop('charges') if 'charges' in updated_data else None
            updated_data.pop('foundation_account') if 'foundation_account' in item else None
            updated_data.pop('bill_date') if 'bill_date' in item else None
            filtered_data = remove_filds(BaselineDataTable, updated_data)
            BaselineDataTable.objects.create(banOnboarded=self.instance, bill_date=self.bill_date,**filtered_data)
    def process_pdf_from_buffer(self):
        logger.info('Extracting data from PDF')
        try:    
            data, acc_info, bill_date_info = self.extract_data_from_pdf()
            self.save_to_base_data_table(data)
            
            self.save_to_portal_info(data=data[0] if type(data) == list else data)
            
            temp_data = data
            temp_df = pd.DataFrame([temp_data])
            if 'Net_Amount' not in temp_df.columns:
                temp_df['Net_Amount'] = 'NA'
                temp_dict = temp_df.to_dict(orient='records')
                new_dict = temp_dict[0]
                self.save_to_batch_report(new_dict,self.vendor_name)
            else:
                self.save_to_batch_report(data, self.vendor_name)
                pass
            print('rex')
            pdf_data, unique_pdf_data,tmp_df = self.extract_total_pdf_data(acc_info,bill_date_info)
            print('brock')
            dir = 'output'
            # i = pd.DataFrame(pdf_data)
            # filename = 't_mobile_category.csv'
            # path = os.path.join(dir,filename)
            # tmp_df.to_csv(path)
            wireless_data = defaultdict(lambda: defaultdict(dict))

            if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
                for idx, row in tmp_df.iterrows():
                    wireless_number = row['wireless number']
                    item_category = str(row['item category']).strip().upper()
                    item_description = str(row['item description']).strip().upper()
                    charges = charges = str(row['charges']).replace("$",'')
                    if pd.notna(item_category) and pd.notna(item_description) and pd.notna(charges):
                        wireless_data[wireless_number][item_category][item_description] = charges
                result_list = [dict(wireless_data)]
                udf = pd.DataFrame(unique_pdf_data)
                if isinstance(udf, pd.DataFrame):
                    udf.rename(columns={'wireless number':'Wireless_number'},inplace=True)
            else:
                if isinstance(tmp_df, pd.DataFrame):
                    tmp_df.rename(columns={'Item Category':'Item_Category','Item Description':'Item_Description'},inplace=True)
                    for idx, row in tmp_df.iterrows():
                        wireless_number = row['Wireless_number'] if 'Wireless_number' in row else None
                        item_category = str(row['Item_Category']).strip().upper() if 'Item_Category' in row else None
                        item_description = str(row['Item_Description']).strip().upper() if 'Item_Description' in row else None
                        charges = str(row['Charges']).replace("$",'') if 'Charges' in row else None
                        if pd.notna(item_category) and pd.notna(item_description) and pd.notna(charges):
                            wireless_data[wireless_number][item_category][item_description] = charges
                result_list = [dict(wireless_data)]
                udf = pd.DataFrame(unique_pdf_data)
            wireless_numbers = []
            charges_objects = []

            # Populate the wireless numbers and charges objects lists
            for entry in result_list:
                for number, charges in entry.items():
                    wireless_numbers.append(number)
                    charges_objects.append(json.dumps(charges))  # Convert dictionary to JSON string for storage

            # Create the DataFrame with two columns: Wireless_number and Charges_Object
            
            obj_df = pd.DataFrame({
                'Wireless_number': wireless_numbers,
                'category_object': charges_objects
            })
            category_obj_df = pd.merge(udf,obj_df,on='Wireless_number',how='left')
            
            category_obj_df['category_object'] = category_obj_df['category_object'].apply(
                lambda x: {"NAN": "NAN"} if pd.isna(x) or x == '' else x
            )
            category_data = category_obj_df.to_dict(orient='records')
            non_cat_df = udf
            non_cat_df['category_object'] = json.dumps({})
            non_categorical_data = non_cat_df.to_dict(orient='records')
            if self.entry_type != "Master Account":
                self.save_to_pdf_data_table(pdf_data)
                print('got here')
                self.save_to_unique_pdf_data_table(unique_pdf_data)
                if self.month == None and self.year == None:
                    if self.baseline_check == True:
                        self.save_to_baseline_data_table(category_data)
                    else:
                        self.save_to_baseline_data_table(non_categorical_data)    
            print('wie gets')
            self.reflect_category_object()
            message = 'file has been processed successfully'
        except Exception as e:
            print(f"Failed to send email notification. Error:",{e})
            message = 'file could not be processed due to invalid format or invalid content'


        subject = 'Notification: File Processing Completed'

        body = f"""
        Dear User,

        We would like to inform you that the following action has been completed: **{message}**.

        You can view the corresponding baseline table at the following link:
        [View Baseline Table](https://mobdash.vercel.app/view/onboard-bill-baseline/{self.sub_company}/{self.vendor_name}/{self.account_number})

        If you have any questions or require further assistance, please do not hesitate to contact us.

        Thank you for your attention.

        Best regards,  
        The Support Team
        """

        # send_custom_email(receiver_mail="gauravdhale09@gmail.com", subject=subject, body=body)
        send_custom_email(receiver_mail=self.email, subject=subject, body=body)
        
            
def remove_filds(model, data):
    valid_fields = {field.name for field in model._meta.get_fields()}

    filtered_data = {key: value for key, value in data.items() if key in valid_fields}

    return filtered_data

