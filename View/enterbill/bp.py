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
from OnBoard.Ban.models import PdfDataTable, UniquePdfDataTable, BaselineDataTable
import pdfplumber
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessBills:
    def __init__(self, buffer_data,instance):
        self.buffer_data = buffer_data
        self.pdf_path = self.buffer_data['pdf_path'] if 'pdf_path' in self.buffer_data else None
        self.company_name = self.buffer_data['company_name'] if 'company_name' in self.buffer_data else None
        self.vendor_name = self.buffer_data['vendor_name'] if 'vendor_name' in self.buffer_data else None
        self.pdf_filename = self.buffer_data['pdf_filename'] if 'pdf_filename' in self.buffer_data else None
        self.month = self.buffer_data['month'] if 'month' in self.buffer_data else None
        self.entry_type = self.buffer_data['entry_type'] if 'entry_type' in self.buffer_data else None
        self.baseline_check = True
        self.location = self.buffer_data['location'] if 'location' in self.buffer_data else None
        self.master_account = self.buffer_data['master_account'] if 'master_account' in self.buffer_data else None
        self.year = self.buffer_data['year'] if 'year' in self.buffer_data else None
        self.types = self.buffer_data['types'] if 'types' in self.buffer_data else None
        # self.email = self.buffer_data['email'] if 'email' in self.buffer_data else None
        self.sub_company = self.buffer_data['sub_company'] if 'sub_company' in self.buffer_data else None
        self.t_mobile_type = self.check_tmobile_type() if 'mobile' in str(self.vendor_name).lower() else 0
        logger.info(f'Processing PDF from buffer: {self.pdf_path}, {self.company_name}, {self.vendor_name}, {self.pdf_filename}')

        self.instance = instance
        self.check = True
    
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
            0
    def extract_data_from_pdf(self):
        print("def extract_data_from_pdf")
        logger.info(f'Extracting data from PDF: {self.pdf_path}')
        at_vendor_list = ['AT&T','AT n T','ATT','at&t','att','at n t']
        t_mobile_list = ['T_Mobile','t-mobile','T-mobile','t_mobile']

        if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
            base_data_df,pdf_df,temp,rox,on,dates,acc_nos = get_all_dataframes_type_1(self.pdf_path)
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
            print(data_dict)
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
            data_dict['company'] = self.company_name
            data_dict['vendor'] = self.vendor_name
            data_dict['pdf_path'] = self.pdf_path
            data_dict['pdf_filename'] = self.pdf_filename
            data_dict['month'] = self.month
            data_dict['year'] = self.year
            data_dict['sub_company'] = self.sub_company
            data_dict['entry_type'] = self.entry_type

            data_dict['location'] = self.location
            data_dict['master_account'] = self.master_account

        return data_dict,acc_info,bill_date_info
    def save_to_base_data_table(self, data):
    
        print("def save_to_base_data_table")
        from django.db import transaction
        from ..models import BaseDataTable
        print(data)
        mapping = {
            "Date_Due":"date_due", 
            "AccountNumber":"accountnumber",
            "billing_address":"Billing_Address",
            "InvoiceNumber":"invoicenumber", 
            "Website":"website",
            "Duration":"duration",
            "Bill_Date":"bill_date",
            "Client_Address":"Remidence_Address",
            "entry_type":"Entry_type",
        }
        if type(data) == dict:
            updated_data = {mapping.get(k, k): v for k, v in data.items()}
            print(updated_data)
            updated_data.pop("foundation_account") if 'foundation_account' in updated_data else None
            filtered_data = remove_filds(BaseDataTable, updated_data)
            BaseDataTable.objects.create(viewuploaded=self.instance, **filtered_data)
        elif type(data) == list:
            for item in data:
                updated_data = {mapping.get(k, k): v for k, v in item.items()}
                filtered_data = filtered_data = remove_filds(BaseDataTable, updated_data)
                BaseDataTable.objects.create(viewuploaded=self.instance, **filtered_data)

    def extract_total_pdf_data(self,acc_info,bill_date):
        print("def extract_total_pdf_data")
        total_dict = None
        result_df = None
        tmp_df = None
        if 'mobile' in str(self.vendor_name).lower():
            print("vendor name is mobile")
            print(self.vendor_name)
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
        print(data_df.columns)
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
            updated_data = {mapping.get(k, k): v for k, v in item.items()}
            filtered_data = remove_filds(PdfDataTable, updated_data)
            
            PdfDataTable.objects.create(viewuploaded=self.instance, **filtered_data)
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
            print(item)
            updated_data = {mapping.get(k, k): v for k, v in item.items()}
            updated_data.pop('charges') if 'charges' in updated_data else None
            updated_data.pop('location') if 'location' in updated_data else None
            updated_data.pop('Note') if 'Note' in updated_data else None
            filtered_data = remove_filds(UniquePdfDataTable, updated_data)
            UniquePdfDataTable.objects.create(viewuploaded=self.instance,**filtered_data)
    def save_to_baseline_data_table(self,data):
        print("saving to baseline_data_table")
        data_df = pd.DataFrame(data)
        if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
            column_mapping = {
                'Wireless_number': 'wireless_number',
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
        # for item in data:
        #     keys = ', '.join([f'"{key}"' for key in item.keys()])
        #     values = ', '.join([f"'{value}'" for value in item.values()])
        #     cursor.execute(f'INSERT INTO myapp_baseline_data_table ({keys}) VALUES ({values})')
        # Assuming `data` is a list of dictionaries containing the records to insert
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
            updated_data.pop('bill_date') if 'bill_date' in updated_data else None
            filtered_data = remove_filds(BaselineDataTable, updated_data)
            BaselineDataTable.objects.create(viewuploaded=self.instance,**filtered_data)
    def process(self):
        print(self.buffer_data)
        logger.info('Extracting data from PDF')
        try:    
            data, acc_info, bill_date_info = self.extract_data_from_pdf()
            

            # self.save_to_base_data_table(data)
            temp_data = data
            temp_df = pd.DataFrame([temp_data])
            if 'Net_Amount' not in temp_df.columns:
                temp_df['Net_Amount'] = 'NA'
                temp_dict = temp_df.to_dict(orient='records')
                new_dict = temp_dict[0]
                #save_to_batch_report(new_dict,vendor_name)
            else:
                #save_to_batch_report(data, vendor_name)
                pass
            print("*********",self.pdf_path, acc_info, self.company_name, self.vendor_name,bill_date_info,self.sub_company)
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
                    item_category = row['item category']
                    item_description = row['item description']
                    charges = row['charges']
                    if pd.notna(item_category) and pd.notna(item_description) and pd.notna(charges):
                        wireless_data[wireless_number][item_category][item_description] = charges
                result_list = [dict(wireless_data)]
                udf = pd.DataFrame(unique_pdf_data)
                udf.rename(columns={'wireless number':'Wireless_number'},inplace=True)
            else:
                tmp_df.rename(columns={'Item Category':'Item_Category','Item Description':'Item_Description'},inplace=True)
                for idx, row in tmp_df.iterrows():
                    wireless_number = row['Wireless_number']
                    item_category = row['Item_Category']
                    item_description = row['Item_Description']
                    charges = row['Charges']
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
                    print("**",type(self.baseline_check), self.baseline_check)
                    if self.baseline_check == True:
                        self.save_to_baseline_data_table(category_data)
                    else:
                        self.save_to_baseline_data_table(non_categorical_data)    
            print('wie gets')
            message = 'file has been processed successfully'
        except Exception as e:
            print(f"Failed to send email notification. Error:",{e})
            message = 'file could not be processed due to invalid format or invalid content'
        sender_email = 'avinashkalmegh93@gmail.com'
        receiver_email = 'kunalkalpande1999@gmail.com'
        subject = 'File Processing Notification'
        body = f"""
        Dear User,
        This is to notify you that the {message} .
        Thank you.
        """
        smtp_server = 'mail.privateemail.com'
        smtp_port = 465
        smtp_username = 'support@disruptionsim.com'
        smtp_password = 'Onesmarter@2023'

        message = MIMEText(body, 'plain')
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = subject

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            print("Email notification sent successfully!")
        except Exception as e:
            print(f"Failed to send email notification. Error: {str(e)}")
    
def remove_filds(model, data):
    valid_fields = {field.name for field in model._meta.get_fields()}

    filtered_data = {key: value for key, value in data.items() if key in valid_fields}

    return filtered_data