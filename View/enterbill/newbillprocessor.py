import pdfplumber
from Scripts.verizon import PDFExtractor, First, Model1, Model2, Model3, Model4
from Scripts.Att import first_page_extractor, Att, process_all
from Scripts.tmobile1 import get_all_dataframes_type_1
from Scripts.tmobile2 import extract_text_from_t_mobile_2

batch_count = '000'
from datetime import datetime
import logging
import sqlite3
import json
import re
from pathlib import Path
import time
import os
import zipfile
import pandas as pd
import io
from io import BytesIO, StringIO
import numpy as np
from collections import defaultdict
from urllib.parse import quote


from OnBoard.Ban.models import PdfDataTable, UniquePdfDataTable, BaselineDataTable, BaseDataTable
from ..models import ProcessedWorkbook, ViewUploadBill
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.files import File
import ast
from sendmail import send_custom_email


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessBills:
    def __init__(self, buffer_data,instance):
        print(buffer_data)
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
        self.email = self.buffer_data['email'] if 'email' in self.buffer_data else None
        self.sub_company = self.buffer_data['sub_company_name'] if 'sub_company_name' in self.buffer_data else None
        self.t_mobile_type = self.check_tmobile_type() if 'mobile' in str(self.vendor_name).lower() else 0
        logger.info(f'Processing PDF from buffer: {self.pdf_path}, {self.company_name}, {self.vendor_name}, {self.pdf_filename}')

        self.instance = instance
        self.check = True
        self.account_number = self.buffer_data['account_number'] if 'account_number' in self.buffer_data else None
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
    def save_to_base_data_table(self, data,remittance_address):
    
        print("def save_to_base_data_table")
        from django.db import transaction
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
            updated_data.pop("foundation_account") if 'foundation_account' in updated_data else None
            filtered_data = remove_filds(BaseDataTable, updated_data)
       
            bill_date = filtered_data.pop('bill_date').replace(',','')
            obj = BaseDataTable.objects.create(viewuploaded=self.instance,bill_date=bill_date,RemittanceAdd=remittance_address, **filtered_data)
            self.account_number = obj.accountnumber
            obj.save()
        elif type(data) == list:
            for item in data:
                updated_data = {mapping.get(k, k): v for k, v in item.items()}
                filtered_data = filtered_data = remove_filds(BaseDataTable, updated_data)
                bill_date = filtered_data.pop('bill_date').replace(',','')
                obj = BaseDataTable.objects.create(viewuploaded=self.instance,bill_date=bill_date,RemittanceAdd=remittance_address, **filtered_data)
                self.account_number = obj.accountnumber
                obj.save()
        return obj
        
    
    def extract_total_pdf_data(self,acc_info):
        print("def extract_total_pdf_data")
        at_vendor_list = ['AT&T','AT n T','ATT','at&t','att','at n t']
        t_mobile_list = ['T_Mobile','t-mobile','T-mobile','t_mobile']
        total_dict = None
        result_df = None
        duplicate_df = None

        if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
            print("t_mobile type 1")
            base_data_df,pdf_df,duplicate_df,in_valid_df,usage_df = get_all_dataframes_type_1(self.pdf_path)
            result_df = pdf_df
            duplicate_df = duplicate_df
            extra_df = in_valid_df
            existing_columns = [
                'wireless number', 'Total Current Charges', 'Recurring Charges', 'Adjustments', 'Usage Charges', 'One Time Charges', 
                'Other Charges', 'Third-party Charges', 'Taxes & Surcharges', 'Account Number', 'Customer Service Number', 
                'Data Plan', 'Address', 'Data Usage (KB)', 'Data Usage (MB)', 'Voice Roaming', 'Messaging Roaming', 
                'Data Roaming (KB)', 'Data Roaming (MB)', 'Data Roaming (GB)', 'User name', 'Invoice number', 'ECPD Profile', 
                'User ID', 'Foundation account', 'item category', 'item description', 'bill_date'
            ]

            # Required columns order
            required_columns = [
                'Wireless Number', 'User Name', 'Account Charges and Credits', 'Usage and Purchase Charges', 'Equipment Charges', 
                'Surcharges and Other Charges and Credits', 'Taxes, Governmental Surcharges and Fees', 'Third-Party Charges (includes Tax)', 
                'Total Charges', 'Voice Plan Usage', 'Messaging Usage', 'Data Usage', 'Voice Roaming', 'Messaging Roaming', 
                'Account_number', 'Group Number', 'User Email', 'Status', 'Cost Center', 'Your Calling Plans', 'Item Category', 
                'Item Type', 'Item Description', 'Share Description', 'Share Voice', 'Share Messaging', 'Share Data', 'Allowance', 
                'Used', 'Billable', 'Charges', 'Order Details', 'Bill Cycle Date', 'Invoice Number', 'ECPD Profile ID', 'User ID', 
                'Data Usage (KB)', 'Data Usage (MB)', 'Data Roaming_Data Roaming (KB)', 'Data Roaming_Data Roaming (MB)', 
                'Data Roaming_Data Roaming (GB)','Voice Plan Usage','Data Usage','Messaging Usage'
            ]

            # Create a mapping from existing columns to required columns
            column_mapping = {
                'wireless number': 'Wireless Number',
                'User name': 'User Name',
                'Total Current Charges': 'Total Charges',
                'Recurring Charges': 'Account Charges and Credits',
                'Usage Charges': 'Usage and Purchase Charges',
                'One Time Charges': 'Equipment Charges',
                'Other Charges': 'Surcharges and Other Charges and Credits',
                'Third-party Charges': 'Third-Party Charges (includes Tax)',
                'Taxes & Surcharges': 'Taxes, Governmental Surcharges and Fees',
                'Account Number': 'Account_number',
                'item category': 'Item Category',
                'item description': 'Item Description',
                'bill_date': 'Bill Cycle Date',
                'ECPD Profile': 'ECPD Profile ID',
                'Customer Service Number': 'Customer Service Number',
                'Data Plan': 'Data Plan',
                'Address': 'Address',
                'Data Usage (KB)': 'Data Usage (KB)',
                'Data Usage (MB)': 'Data Usage (MB)',
                'Voice Roaming': 'Voice Roaming',
                'Messaging Roaming': 'Messaging Roaming',
                'Data Roaming (KB)': 'Data Roaming_Data Roaming (KB)',
                'Data Roaming (MB)': 'Data Roaming_Data Roaming (MB)',
                'Data Roaming (GB)': 'Data Roaming_Data Roaming (GB)',
                'User ID': 'User ID',
                'Foundation account': 'Foundation account',
                'Invoice number': 'Invoice Number'
            }

            # Reorder the columns in the DataFrame according to the required columns
            mapped_columns = {v: k for k, v in column_mapping.items()}
            reordered_columns = [mapped_columns.get(col, col) for col in required_columns]
            reordered_df = pdf_df.reindex(columns=reordered_columns)

            # Add missing columns with default values (NaN or other default value)
            # Reorder the DataFrame to match the exact order of required columns
            reordered_df.rename(columns={'wireless number':'Wireless Number','User name':'User Name','Recurring Charges':'Account Charges and Credits','Usage Charges': 'Usage and Purchase Charges','One Time Charges': 'Equipment Charges','Other Charges': 'Surcharges and Other Charges and Credits','Taxes & Surcharges': 'Taxes, Governmental Surcharges and Fees','Third-party Charges': 'Third-Party Charges (includes Tax)','Total Current Charges': 'Charges',
                    'item category': 'Item Category',
                'item description': 'Item Description',
                'bill_date': 'Bill Cycle Date',
                'ECPD Profile': 'ECPD Profile ID','Invoice number': 'Invoice Number'},inplace=True)
            for col in required_columns:
                if col not in reordered_df.columns:
                    reordered_df[col] = pd.NA
            columns_order_new = [
                'Wireless Number', 'User Name', 'Account Charges and Credits', 'Usage and Purchase Charges',
                'Equipment Charges', 'Surcharges and Other Charges and Credits', 'Taxes, Governmental Surcharges and Fees',
                'Third-Party Charges (includes Tax)', 'Total Charges', 'Voice Plan Usage', 'Messaging Usage',
                'Data Usage', 'Voice Roaming', 'Messaging Roaming', 'Account_number', 'Group Number', 'User Email',
                'Status', 'Cost Center', 'Your Calling Plans', 'Item Category', 'Item Type', 'Item Description',
                'Share Description', 'Share Voice', 'Share Messaging', 'Share Data', 'Allowance', 'Used', 'Billable',
                'Charges', 'Order Details', 'Bill Cycle Date', 'Invoice Number', 'ECPD Profile ID', 'User ID',
                'Data Usage (KB)', 'Data Usage (MB)', 'Data Roaming_Data Roaming (KB)', 'Data Roaming_Data Roaming (MB)',
                'Data Roaming_Data Roaming (GB)'
            ]

            new_order = [col for col in columns_order_new if col in reordered_df.columns] + \
                        [col for col in reordered_df.columns if col not in columns_order_new]

            reordered_df = reordered_df[new_order]
            pdf_df = reordered_df
            result_df = pdf_df
            existing_columns = [
                'wireless number', 'charges', 'account number', 'address', 'item category', 'item description', 'data', 'minutes', 
                'messages', 'date', 'Recurring Charges', 'Adjustments', 'Usage Charges', 'One Time Charges', 'Other Charges', 
                'Third-party Charges', 'Taxes & Surcharges', 'Total Current Charges', 'Account Number', 'Customer Service Number', 
                'Data Plan', 'Address', 'Data Usage (KB)', 'Data Usage (MB)', 'Voice Roaming', 'Messaging Roaming', 
                'Data Roaming (KB)', 'Data Roaming (MB)', 'Data Roaming (GB)', 'User name', 'Invoice number', 'ECPD Profile', 
                'User ID', 'Foundation account'
            ]
            target_columns = [
            'Group Number','User Email', 'Status', 
            'Cost Center', 'Account Charges and Credits', 'Item Type', 
            'Share Description', 'Share Voice', 'Share Messaging', 'Share Data', 'Allowance', 'Used', 'Billable' ,
            'Order Details'
            ]

            # Create a mapping from existing columns to target columns
            column_mapping = {
                'wireless number': 'wireless number',
                'charges': 'charges',
                'account number': 'account number',
                'address': 'address',
                'item category': 'item category',
                'item description': 'item description',
                'data': 'data',
                'minutes': 'minutes',
                'messages': 'messages',
                'date': 'date',
                'Recurring Charges': 'Recurring Charges',
                'Adjustments': 'Adjustments',
                'Usage Charges': 'Usage Charges',
                'One Time Charges': 'One Time Charges',
                'Other Charges': 'Other Charges',
                'Third-party Charges': 'Third-party Charges',
                'Taxes & Surcharges': 'Taxes & Surcharges',
                'Total Current Charges': 'Total Current Charges',
                'Account Number': 'Account Number',
                'Customer Service Number': 'Customer Service Number',
                'Data Plan': 'Data Plan',
                'Address': 'Address',
                'Data Usage (KB)': 'Data Usage (KB)',
                'Data Usage (MB)': 'Data Usage (MB)',
                'Voice Roaming': 'Voice Roaming',
                'Messaging Roaming': 'Messaging Roaming',
                'Data Roaming (KB)': 'Data Roaming (KB)',
                'Data Roaming (MB)': 'Data Roaming (MB)',
                'Data Roaming (GB)': 'Data Roaming (GB)',
                'User name': 'User name',
                'Invoice number': 'Invoice number',
                'ECPD Profile': 'ECPD Profile',
                'User ID': 'User ID',
                'Foundation account': 'Foundation account'
            }

            # Reorder the columns in the DataFrame according to the target columns
            reordered_columns = [column_mapping[col] for col in existing_columns if col in column_mapping]
            reordered_df = duplicate_df[reordered_columns]
            # Add missing columns with default values (NaN or other default value)
            for col in target_columns:
                if col not in reordered_df.columns:
                    reordered_df[col] = pd.NA

            # Reorder the DataFrame to match the exact order of target columns
            reordered_df.rename(columns={'wireless number': 'Wireless Number','charges': 'Charges',
                'account number': 'Account Number',
                'item category': 'Item Category',
                'item description': 'Item Description','charges':'Charges','date':'Bill Cycle Date','Invoice number':"Invoice Number",'Foundation account': 'Foundation Account','Total Current Charges':'Total Charges','User name':'User Name','Data Plan':'Plans'},inplace=True)
            columns_order = [
                'Foundation Account', 'Account Number', 'Group Number', 'Wireless Number',
                'User Email', 'Status', 'Cost Center', 'Account Charges and Credits', 
                'Plans', 'Item Category', 'Item Type', 'Item Description', 
                'Share Description', 'Share Voice', 'Share Messaging', 'Share Data', 
                'Allowance', 'Used', 'Billable', 'Charges', 'Order Details', 
                'Bill Cycle Date', 'Invoice Number', 'User Name_User_name_x', 
                'Usage and Purchase Charges', 'Equipment Charges', 
                'Surcharges and Other Charges and Credits', 
                'Taxes Governmental Surcharges and Fees', 
                'Third Party Charges includes Tax', 'Total Charges', 
                'Voice Plan Usage', 'Messaging Usage', 'Data Usage (GB)', 
                'User Name_User_name_y', 'ECPD Profile ID', 'User ID', 
                'Data Usage (KB)', 'Data Usage (MB)', 'Voice Roaming', 
                'Messaging Roaming', 'Data Roaming (KB)', 'Data Roaming (MB)', 
                'Data Roaming (GB)'
            ]

            new_order = [col for col in columns_order if col in reordered_df.columns] + \
                        [col for col in reordered_df.columns if col not in columns_order]

            reordered_df = reordered_df[new_order]
            duplicate_df = reordered_df
        
        elif 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 2:
            print("tmobile type 2")
            unique_df,base_data_df,detail_df = extract_text_from_t_mobile_2(self.pdf_path)
            result_df = unique_df
            duplicate_df = detail_df

            
        elif 'verizon' in str(self.vendor_name).lower():

            extractor = Model4(self.pdf_path,acc_info)

            print("class model4 ends here")
            result,duplicate_dff = extractor.process_pdf()
            temp_result_df = result
            df_unique = temp_result_df.drop_duplicates(subset=['Wireless_number'])
            df_unique_dict = df_unique.to_dict(orient='records')
            total_dict = df_unique_dict
            result_df = result
            duplicate_df = duplicate_dff
            temp_result_df = result
            duplicate = duplicate_dff
            acc = temp_result_df.at[0,'Total_Charges']
            nacc = acc.replace('$','')
            temp_result_df.at[0,'Charges'] = nacc
            target_columns = [
                'Wireless Number', 'User Name', 'Account Charges and Credits', 'Page Number', 'Monthly Charges', 
                'Usage and Purchase Charges', 'Equipment Charges', 'Surcharges and Other Charges and Credits', 
                'Taxes, Governmental Surcharges and Fees', 'Third-Party Charges (includes Tax)', 'Total Charges', 
                'Voice Plan Usage', 'Messaging Usage', 'Data Usage', 'Voice Roaming', 'Messaging Roaming', 'Data Roaming'
            ]

            rename_mapping = {
                'Wireless_number': 'Wireless Number', 'User_name_x': 'User Name', 'Monthly_Charges': 'Monthly Charges', 
                'Usage_and_Purchase_Charges': 'Usage and Purchase Charges', 'Equipment_Charges': 'Equipment Charges',
                'Surcharges_and_Other_Charges_and_Credits': 'Surcharges and Other Charges and Credits',
                'Taxes_Governmental_Surcharges_and_Fees': 'Taxes, Governmental Surcharges and Fees',
                'Third_Party_Charges_includes_Tax': 'Third-Party Charges (includes Tax)', 'Total_Charges': 'Total Charges',
                'Voice_Plan_Usage': 'Voice Plan Usage', 'Messaging_Usage': 'Messaging Usage', 
                'Data Usage(GB)': 'Data Usage', 'Voice Roaming': 'Voice Roaming', 'Messaging Roaming': 'Messaging Roaming',
                'Data Roaming (KB)': 'Data Roaming', 'Data Roaming (MB)': 'Data Roaming', 'Data Roaming (GB)': 'Data Roaming'
            }

            # Check for potential duplicate column names after renaming
            renamed_columns = [rename_mapping.get(col, col) for col in temp_result_df.columns]
            duplicates = {col for col in renamed_columns if renamed_columns.count(col) > 1}

            # Create a new rename mapping to avoid duplicates
            unique_rename_mapping = {}
            for col in temp_result_df.columns:
                new_name = rename_mapping.get(col, col)
                if new_name in duplicates:
                    unique_rename_mapping[col] = f"{new_name}_{col}"  # Append original column name to make it unique
                else:
                    unique_rename_mapping[col] = new_name

            # Rename the columns
            temp_result_df = temp_result_df.rename(columns=unique_rename_mapping)

            # Ensure all target columns are present in the DataFrame
            all_columns = list(unique_rename_mapping.values())
            reordered_columns = [col for col in target_columns if col in all_columns] + [col for col in temp_result_df.columns if col not in target_columns]

            temp_result_df = temp_result_df.reindex(columns=reordered_columns)
            columns_to_drop = [
                'Monthly Charges','Foundation Account','User_name_y'
            ]
            
            existing_columns = [col for col in columns_to_drop if col in temp_result_df.columns]
            if existing_columns:
                temp_result_df.drop(columns=existing_columns, inplace=True)
            temp_result_df.replace('NA','',inplace=True)
            duplicate.drop(columns=['Monthly_Charges'],inplace=True)
            acc = duplicate.at[0,'Total_Charges']
            nacc = acc.replace('$','')
            duplicate.at[0,'Charges'] = nacc
            target_columns = [
                'Foundation Account', 'Account Number', 'Group Number', 'User Name', 'Wireless Number', 'User Email', 
                'Status', 'Cost Center', 'Account Charges and Credits', 'Plans', 'Item Category', 'Item Type', 
                'Item Description', 'Share Description', 'Share Voice', 'Share Messaging', 'Share Data', 'Allowance', 
                'Used', 'Billable', 'Charges', 'Order Details', 'Bill Cycle Date', 'Invoice Number'
            ]

            rename_mapping = {
                'Wireless_number': 'Wireless Number', 'User_name_x': 'User Name', 'Account_number': 'Account Number', 
                'User_name_y': 'User Name', 'Your Calling Plans': 'Plans', 'Data Usage(GB)': 'Data Usage (GB)',
                'Usage_and_Purchase_Charges': 'Usage and Purchase Charges', 'Equipment_Charges': 'Equipment Charges',
                'Surcharges_and_Other_Charges_and_Credits': 'Surcharges and Other Charges and Credits',
                'Taxes_Governmental_Surcharges_and_Fees': 'Taxes Governmental Surcharges and Fees',
                'Third_Party_Charges_includes_Tax': 'Third Party Charges includes Tax', 'Total_Charges': 'Total Charges',
                'Voice_Plan_Usage': 'Voice Plan Usage', 'Messaging_Usage': 'Messaging Usage',
            }

            # Check for potential duplicate column names after renaming
            renamed_columns = [rename_mapping.get(col, col) for col in duplicate.columns]
            duplicates = {col for col in renamed_columns if renamed_columns.count(col) > 1}

            # Create a new rename mapping to avoid duplicates
            unique_rename_mapping = {}
            for col in duplicate.columns:
                new_name = rename_mapping.get(col, col)
                if new_name in duplicates:
                    unique_rename_mapping[col] = f"{new_name}_{col}"  # Append original column name to make it unique
                else:
                    unique_rename_mapping[col] = new_name

            # Rename the columns
            duplicate = duplicate.rename(columns=unique_rename_mapping)

            # Ensure all target columns are present in the DataFrame
            all_columns = list(unique_rename_mapping.values())
            reordered_columns = [col for col in target_columns if col in all_columns] + [col for col in duplicate.columns if col not in target_columns]

            duplicate = duplicate.reindex(columns=reordered_columns)
            duplicate.replace('NA','',inplace=True)
            result_df = temp_result_df
            duplicate_df = duplicate
        else:
            final_df, unique_df,usage_df, initial_df = process_all(self.pdf_path)
            unique_df['Wireless_number'] = unique_df['Wireless_number'].astype(str).str.replace('.', '-', regex=False)
            final_df['Wireless_number'] = final_df['Wireless_number'].astype(str).str.replace('.', '-', regex=False)
            result_df = unique_df
            duplicate_df = final_df
        return result_df,duplicate_df
    def get_cust_data_from_db(self, acc_no):
        print("def get_cust_data_from_db")
        account_number = acc_no

        # Fetch data using Django ORM
        data = list(UniquePdfDataTable.objects.filter(account_number=account_number)
                    .values('wireless_number', 'user_name', 'cost_center', 'total_charges'))

        # Create DataFrame
        columns = ['wireless_number', 'user_name', 'cost_center', 'total_charges']
        df = pd.DataFrame(data, columns=columns)

        if df['cost_center'].isnull().all():
            print('empty_cost_center')
            df = df.drop('cost_center', axis=1)
            return df
        else:
            df['total_charges'] = df['total_charges'].replace('[\$,]', '', regex=True).astype(float)

            # Group by cost_center and sum total_charges
            grouped_df = df.groupby('cost_center')['total_charges'].sum().reset_index()
            grouped_df.columns = ['cost_center', 'sum_of_total_current_charges']

            # Merge grouped data with original DataFrame
            result_df = pd.merge(df, grouped_df, on='cost_center', how='left')
            result_df['Row_labels'] = result_df['cost_center']
            result_df = result_df[['wireless_number', 'user_name', 'cost_center', 'total_charges', 'Row_labels', 'sum_of_total_current_charges']]

            return result_df
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
    def extract_for_lines(self,acc_info,bill_date):
        print("Extract lines====",acc_info)
        print("def extract_for_lines")
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
            df_unique['account_number'] = acc_info
            df_unique_dict = df_unique.to_dict(orient='records')
            total_dict = df_unique_dict
            result_df = result
        else:
            df_unique,final_df,usage_df,tmp_df = process_all(self.pdf_path)
            df_unique['Wireless_number'] = df_unique['Wireless_number'].astype(str).str.replace('.', '-', regex=False)
            final_df['Wireless_number'] = final_df['Wireless_number'].astype(str).str.replace('.', '-', regex=False)
            tmp_df['Wireless_number'] = tmp_df['Wireless_number'].astype(str).str.replace('.', '-', regex=False)
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
            updated_data = {mapping.get(k, k): v for k, v in item.items()}
            filtered_data = remove_filds(PdfDataTable, updated_data)
            
            PdfDataTable.objects.create(viewuploaded=self.instance, **filtered_data)
    
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
            filtered_data = remove_filds(UniquePdfDataTable, updated_data)
            UniquePdfDataTable.objects.create(viewuploaded=self.instance,**filtered_data)
    
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
            filtered_data = remove_filds(BaselineDataTable, updated_data)
            BaselineDataTable.objects.create(viewuploaded=self.instance,**filtered_data)
        
    def process(self):
        logger.info('Extracting data from PDF')
        xlsx_first_dict, acc_info, bill_date_info = self.extract_data_from_pdf()

        onboarded = BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).filter(sub_company=self.sub_company, vendor=self.vendor_name, accountnumber=self.account_number).first()

        baseinstance = self.save_to_base_data_table(xlsx_first_dict, remittance_address=onboarded.RemittanceAdd)
        

        bill_main_id = baseinstance.viewuploaded.id

        onboarded_id = onboarded.banOnboarded

        if isinstance(bill_date_info, list):
            bill_date_info = bill_date_info[0]
        xlsx_unique, xlsx_duplicate = self.extract_total_pdf_data(acc_info)

        bill_date_info = bill_date_info.replace(",","")
        print(len(xlsx_unique))
        print(xlsx_unique.columns)
        print(len(xlsx_duplicate))
        print(xlsx_duplicate.columns)
        print("accc=====>", acc_info, type(acc_info))
        if isinstance(acc_info, list):
            acc_info = acc_info[0]
    
        cust_data_df = self.get_cust_data_from_db(acc_info)
        pdf_data, unique_pdf_data,tmp_df = self.extract_for_lines(acc_info, bill_date_info)
        print(type(pdf_data), type(unique_pdf_data),type(tmp_df))
        wireless_data = defaultdict(lambda: defaultdict(dict))
        if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
            for idx, row in tmp_df.iterrows():
                wireless_number = row['wireless number']
                item_category = str(row['item category']).strip().upper()
                item_description = str(row['item description']).strip().upper()
                charges = str(row['charges']).replace("$",'')
                if pd.notna(item_category) and pd.notna(item_description) and pd.notna(charges):
                    wireless_data[wireless_number][item_category][item_description] = charges
            result_list = [dict(wireless_data)]
            udf = pd.DataFrame(unique_pdf_data)
            udf.rename(columns={'wireless number':'Wireless_number'},inplace=True)
        else:
            tmp_df.rename(columns={'Item Category':'Item_Category','Item Description':'Item_Description'},inplace=True)
            for idx, row in tmp_df.iterrows():
                wireless_number = row['Wireless_number']
                item_category = str(row['Item_Category']).strip().upper() if 'Item_Category' in row else None
                item_description = str(row['Item_Description']).strip().upper() if 'Item_Description' in row else None
                charges = str(row['Charges']).replace("$",'')
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
            print("**",type(self.baseline_check), self.baseline_check)
            if self.baseline_check == True:
                self.save_to_baseline_data_table(category_data)
            else:
                self.save_to_baseline_data_table(non_categorical_data)    
        print('wie gets')
        message = 'file has been processed successfully'
        print(len(pdf_data), len(unique_pdf_data), len(tmp_df))
        try:
            xlsx_first_df = pd.DataFrame(xlsx_first_dict)
        except Exception:
            xlsx_first_df = pd.DataFrame(xlsx_first_dict, index=[0])
        print()
        workbook = self.dataframe_to_excel(xlsx_first_df, xlsx_unique, xlsx_duplicate, cust_data_df)
        print(self.pdf_filename)
        workbook_name = str(self.pdf_filename).split("/")[-1].replace(".pdf", ".xlsx")
        print(workbook_name)
        
        # Define file path inside MEDIA_ROOT
        output_dir = os.path.join(settings.MEDIA_ROOT, "ViewUploadedBills")
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, workbook_name)
        if self.entry_type != "Master Account":
            pass
        
        # self.reflect_non_bill_data(onboarded_id,bill_main_id)
        self.reflect_uniquetable_non_bill_data(bill_main_id=bill_main_id, onboarded_id=onboarded_id)
        self.reflect_baselinetable_non_bill_data(bill_main_id=bill_main_id, onboarded_id=onboarded_id)
        self.add_tag_to_dict(bill_main_id)
        self.reflect_category_object(bill_main_id)
        self.check_baseline_approved(UniquePdfDataTable, bill_main_id)
        self.check_baseline_approved(BaselineDataTable, bill_main_id)

        account_obj = BaselineDataTable.objects.filter(sub_company=self.sub_company, vendor=self.vendor_name, account_number=self.account_number).filter(viewuploaded=self.instance)
        approved_wireless_list = account_obj.values_list('is_baseline_approved', flat=True)

        baseinstance.is_baseline_approved = False if False in list(approved_wireless_list) else True
        try:
            with open(output_file_path, "wb") as f:
                f.write(workbook.getvalue())

            # Create ProcessedWorkbook instance (WITHOUT setting the FileField yet)
            processed_workbook = ProcessedWorkbook(
                uploadbill=self.instance,
                account_number=acc_info,
                vendor_name=self.vendor_name,
                company_name=self.company_name,
                sub_company_name=self.sub_company,
                workbook_name=workbook_name,
                bill_date_info=bill_date_info
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

            message = 'file has been processed successfully'
        except Exception as e:
            print(e)
            message = 'file could not be processed due to invalid format or invalid content'

        subject = 'Notification: File Processing Completed'
        encoded_vendor = quote(self.vendor_name)
        encoded_bill_date = quote(bill_date_info)
        link = f"https://mobdash.vercel.app/view/view-bill-baseline/{self.sub_company}/{encoded_vendor}/{self.account_number}/{encoded_bill_date}"

        body = f"""
        Dear User,

        We would like to inform you that the following action has been completed: **{message}**.

        You can view the corresponding baseline table at the following link:
        [View Baseline Table] {link}

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

from addon import parse_until_dict
def tagging(baseline_data, bill_data):
    baseline_data = parse_until_dict(baseline_data)
    bill_data = parse_until_dict(bill_data)
    def compare_and_tag(base, bill):
        for key in list(bill.keys()):
            if key not in base:
                bill[key] = {"amount": f'{bill[key]}', "approved": True}
                continue
            base_val = base[key]
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
