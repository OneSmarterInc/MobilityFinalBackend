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
from .scripts.verizon import PDFExtractor, First, Model1, Model2, Model3, Model4
from .scripts.Att import First_Page_Extractor, Att, process_all
from .scripts.t_mobile1 import get_all_dataframes
from .scripts.t_mobile2 import extract_text_from_t_mobile
import pdfplumber
from datetime import datetime
import logging
from django.conf import settings
from django.core.files import File
from OnBoard.Ban.models import UniquePdfDataTable
from ..models import ProcessedWorkbook


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessBills:
    def __init__(self, buffer_data, instance):
        self.buffer_data = buffer_data
        self.instance = instance
        self.vendor_name = self.buffer_data['vendor_name']
        self.pdf_path =  self.buffer_data['pdf_path']
        self.pdf_filename = self.buffer_data['pdf_filename']
        self.company_name = self.buffer_data['company_name']
        self.sub_company_name = self.buffer_data['sub_company_name']
        self.types = self.buffer_data['types']
        self.t_mobile_type = self.check_tmobile_type() if 'mobile' in str(self.vendor_name).lower() else 0

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
        at_vendor_list = ['AT&T', 'AT n T', 'ATT', 'at&t', 'att', 'at n t']
        t_mobile_list = ['T_Mobile', 't-mobile', 'T-mobile', 't_mobile']
        print(self.types)
        if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
            print("t_mobile type 1")
            print('hallo i am in')
            base_data_df,pdf_df,temp,rox,on = get_all_dataframes(self.t_mobile_type)
            data_dict = base_data_df.to_dict(orient='records')
            acc_info = '12345678'
            bill_date_info = 'jan1'
            data_dict = data_dict[0]
            data_dict['vendor'] = self.vendor_name
            data_dict['pdf_path'] = self.pdf_path
            data_dict['pdf_filename'] = self.pdf_filename
        elif 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 2:
            print("t_mobile type 2")
            unique_df, base_df, temp_check = extract_text_from_t_mobile(self.pdf_path)
            print("extraction ends")

            data_dict_list = base_df.to_dict(orient='records')  # List of dictionaries
            print(data_dict_list)

            acc_info = '12345678'
            bill_date_info = 'jan1'

            # Add new keys to each dictionary in the list
            for data_dict in data_dict_list:
                data_dict['vendor'] = self.vendor_name
                data_dict['pdf_path'] = self.pdf_path
                data_dict['pdf_filename'] = self.pdf_filename    

            print(data_dict_list)
        
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
                entry['vendor'] = self.vendor_name
                entry['pdf_path'] = self.pdf_path
                entry['pdf_filename'] = self.pdf_filename
        else:
            first_obj = First_Page_Extractor(self.pdf_path)
            data_dict = first_obj.first_page_data_func()
            acc_info = first_obj.get_acc_info()
            bill_date_info = first_obj.get_bill_date_info()
            data_dict['vendor'] = self.vendor_name
            data_dict['pdf_path'] = self.pdf_path
            data_dict['pdf_filename'] = self.pdf_filename
            
        return data_dict, acc_info, bill_date_info
    def extract_total_pdf_data(self, acc_info):
        print("def extract_total_pdf_data")
        at_vendor_list = ['AT&T','AT n T','ATT','at&t','att','at n t']
        t_mobile_list = ['T_Mobile','t-mobile','T-mobile','t_mobile']
        total_dict = None
        result_df = None
        duplicate_df = None
        if 'mobile' in str(self.vendor_name).lower() and self.t_mobile_type == 1:
            print("t_mobile type 1")
            base_data_df,pdf_df,duplicate_df,in_valid_df,usage_df = get_all_dataframes(self.pdf_path)
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
            unique_df,base_data_df,detail_df = extract_text_from_t_mobile(self.pdf_path)
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
            final_df,unique_df = process_all(self.pdf_path)
            result_df = unique_df
            duplicate_df = final_df
        return result_df,duplicate_df
    def get_cust_data_from_db(self,acc_no):
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
   
    def dataframe_to_excel(self,df1, df2, df3, df4):
        print("def dataframe_to_excel")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df1.to_excel(writer, sheet_name='Sheet1', index=False)
            df2.to_excel(writer, sheet_name='Sheet2', index=False)
            df3.to_excel(writer, sheet_name='Sheet3', index=False)
            df4.to_excel(writer, sheet_name='Sheet4', index=False)
        output.seek(0)
        return output
    
    def process(self):
        xlsx_first_dict, acc_info, bill_date_info = self.extract_data_from_pdf()

        if isinstance(bill_date_info, list):
            bill_date_info = bill_date_info[0]

        xlsx_unique, xlsx_duplicate = self.extract_total_pdf_data(acc_info)

        acc_info = str(acc_info[0]) if isinstance(acc_info, list) else str(acc_info)

        cust_data_df = self.get_cust_data_from_db(acc_info)

        try:
            xlsx_first_df = pd.DataFrame(xlsx_first_dict)
        except Exception:
            xlsx_first_df = pd.DataFrame(xlsx_first_dict, index=[0])

        workbook = self.dataframe_to_excel(xlsx_first_df, xlsx_unique, xlsx_duplicate, cust_data_df)
        
        print(self.pdf_filename)
        workbook_name = str(self.pdf_filename).split("/")[-1].replace(".pdf", ".xlsx")
        print(workbook_name)
        
        # Define file path inside MEDIA_ROOT
        output_dir = os.path.join(settings.MEDIA_ROOT, "ViewUploadedBills")
        os.makedirs(output_dir, exist_ok=True)
        output_file_path = os.path.join(output_dir, workbook_name)

        # Save the workbook to a file
        try:
            # Save workbook data to memory
            workbook_data = workbook.getvalue()
            
            # Create Django File object
            django_file = File(io.BytesIO(workbook_data), name=workbook_name)

            # Create ProcessedWorkbook instance
            processed_workbook = ProcessedWorkbook(
                uploadbill=self.instance,
                account_number=acc_info,
                vendor_name=self.vendor_name,
                company_name=self.company_name,
                sub_company_name=self.sub_company_name,
                workbook_name=workbook_name,
                bill_date_info=bill_date_info,
                output_file=django_file  # Directly assign File object
            )

            # Assign to self.instance as well
            self.instance.output_file = django_file
            
            # Save models
            processed_workbook.save()
            self.instance.save()

        except Exception as e:
            print(f"Error: {e}")
