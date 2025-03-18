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
import psycopg2
import logging
import smtplib
from email.mime.text import MIMEText
import numpy as np
import pdfplumber
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

t_mobile_type = 0


def extract_data_from_pdf(pdf_path,company_nm,vendor_nm,pdf_filename,month,year,sub_company,types,entry_type,location,master_account):

    logger.info(f'Extracting data from PDF: {pdf_path}')
    at_vendor_list = ['AT&T','AT n T','ATT','at&t','att','at n t']
    t_mobile_list = ['T_Mobile','t-mobile','T-mobile','t_mobile']
    # if vendor_nm in t_mobile_list:
    #     base_data_df,pdf_df,duplicate_df,in_valid_df,usage_df = get_all_dataframes(pdf_path)
    #     data_dict = base_data_df.to_dict(orient='records')
    #     data_dict = data_dict[0]
    #     acc_info = data_dict['accountnumber']
    #     bill_date_info = None
    #     data_dict['company'] = company_nm
    #     data_dict['vendor'] = vendor_nm
    #     data_dict['pdf_path'] = pdf_path
    #     data_dict['pdf_filename'] = pdf_filename
    #     data_dict['month'] = month
    #     data_dict['year'] = year
    #     data_dict['sub_company_name'] = sub_company
    if vendor_nm in t_mobile_list and t_mobile_type == 1:
        base_data_df,pdf_df,temp,rox,on,dates,acc_nos = get_all_dataframes_type_1(pdf_path)
        base_data_df.drop(columns=['Previous Balance','Grand Total','Monthly Recurring Charges','Other Charges', 'Taxes & Surcharges'],inplace=True)
        base_data_df.rename(columns={'Account Number':'AccountNumber','Address':"Billing Address",'Vendor_Address':'Remidence_Address'},inplace=True)
        base_data_df.columns = base_data_df.columns.str.replace(' ', '_')
        data_dict = base_data_df.to_dict(orient='records')
        acc_info = acc_nos
        bill_date_info = dates
        data_dict = data_dict[0]
        data_dict['company'] = company_nm
        data_dict['vendor'] = vendor_nm
        data_dict['pdf_path'] = pdf_path
        data_dict['pdf_filename'] = pdf_filename
        data_dict['month'] = month
        data_dict['year'] = year
        data_dict['sub_company'] = sub_company
        data_dict['Bill_Date'] = dates
        data_dict['entry_type'] = entry_type

        data_dict['location'] = location
        data_dict['master_account'] = master_account

    elif vendor_nm in t_mobile_list and types == 'second':
        unique_df,base_df,temp_check = extract_text_from_t_mobile_2(pdf_path)
        base_df.rename(columns={'account.number':'AccountNumber','invoice.number':'InvoiceNumber'},inplace=True)
        data_dict = base_df.to_dict(orient='records')
        acc_info = '12345678'
        bill_date_info = 'jan1'
        data_dict = data_dict[0]
        print(data_dict)
        data_dict['company'] = company_nm
        data_dict['vendor'] = vendor_nm
        data_dict['pdf_path'] = pdf_path
        data_dict['pdf_filename'] = pdf_filename
        data_dict['month'] = month
        data_dict['year'] = year
        data_dict['sub_company'] = sub_company   
    elif vendor_nm in at_vendor_list:
        first_obj = first_page_extractor(pdf_path)
        data_dict = first_obj.first_page_data_func()
        acc_info = first_obj.get_acc_info()
        bill_date_info = first_obj.get_bill_date_info()
        data_dict['company'] = company_nm
        data_dict['vendor'] = vendor_nm
        data_dict['pdf_path'] = pdf_path
        data_dict['pdf_filename'] = pdf_filename
        data_dict['month'] = month
        data_dict['year'] = year
        data_dict['sub_company'] = sub_company
        data_dict['entry_type'] = entry_type

        data_dict['location'] = location
        data_dict['master_account'] = master_account

    else:    
        lines_to_extract = [2, 3, 4, 5]
        extractor = PDFExtractor(pdf_path)
        extractor.extract_data()
        extractor.process_pdf(lines_to_extract)
        data = extractor.get_result_df()
        acc_info = extractor.get_accounts_info()
        bill_date_info = extractor.get_bill_date()
        data_dict = data.to_dict(orient='records')
        for entry in data_dict:
            entry['company'] = company_nm
            entry['vendor'] = vendor_nm
            entry['pdf_path'] = pdf_path
            entry['pdf_filename'] = pdf_filename
            entry['month'] = month
            entry['year'] = year
            entry['sub_company'] = sub_company
            entry['entry_type'] = entry_type

            entry['location'] = location
            entry['master_account'] = master_account

    return data_dict,acc_info,bill_date_info
def check_tmobile_type(Billpath):
    print("def check_tmobile_type")
    Lines = []
    with pdfplumber.open(Billpath) as pdf:
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
        None
def extract_total_pdf_data(pdf_path,acc_info,company_nm,vendor_nm,bill_date,sub_com,types,location):
    at_vendor_list = ['AT&T','AT n T','ATT','at&t','att','at n t']
    t_mobile_list = ['T_Mobile','t-mobile','T-mobile','t_mobile']
    total_dict = None
    result_df = None
    tmp_df = None
    if 'mobile' in str(vendor_nm).lower():
        print("vendor name is mobile")
        print(vendor_nm)
        tmobile_type = check_tmobile_type(pdf_path)
        if tmobile_type == 1:
            print('got first')
            print('>>>>>>>>>>>>><<<<<<<<<<<<<<>>>>>>>>>>>>><<<<<<<<<<<>>>>>>>>>>>')
            base_data_df,pdf_df,tmp_df,in_valid_df,usage_df,dates,acc_nos = get_all_dataframes_type_1(pdf_path)
            print('>>>>>>>>>>>>>>>qwertyui<<<<<<<<<<<<')
            pdf_df['account_number'] = acc_info
            total_dict = pdf_df.to_dict(orient='records')
            result_df = pdf_df
        elif tmobile_type == 2:
            print('got second')
            unique_df,base_data_df,detail_df = extract_text_from_t_mobile_2(pdf_path)
            total_dict = unique_df.to_dict(orient='records')
            result_df = unique_df
        else:
            return {'message': 'Invalid tmobile type', 'Error' : 1}
    # if vendor_nm in t_mobile_list and types =='first':
    #     print('got first')
    #     print('>>>>>>>>>>>>><<<<<<<<<<<<<<>>>>>>>>>>>>><<<<<<<<<<<>>>>>>>>>>>')
    #     base_data_df,pdf_df,tmp_df,in_valid_df,usage_df,dates,acc_nos = get_all_dataframes_type_1(pdf_path)
    #     print('>>>>>>>>>>>>>>>qwertyui<<<<<<<<<<<<')
    #     pdf_df['account_number'] = acc_info
    #     total_dict = pdf_df.to_dict(orient='records')
    #     result_df = pdf_df
    # elif vendor_nm in t_mobile_list and types == 'second':
    #     print('got second')
    #     unique_df,base_data_df,detail_df = extract_text_from_t_mobile_2(pdf_path)
    #     total_dict = unique_df.to_dict(orient='records')
    #     result_df = unique_df
    # elif vendor_nm in at_vendor_list:
    #     df_unique,final_df,usage_df,tmp_df = process_all(pdf_path)
    #     df_unique['account_number'] = acc_info
    #     final_df['account_number'] = acc_info
    #     df_unique_dict = df_unique.to_dict(orient='records')
    #     total_dict = df_unique_dict
    #     result_df = final_df
    elif 'verizon' in str(vendor_nm).lower():
        extractor = Model4(pdf_path,acc_info)
        result,tmp_df = extractor.process_pdf()
        temp_result_df = result
        df_unique = temp_result_df.drop_duplicates(subset=['Wireless_number'])
        df_unique_dict = df_unique.to_dict(orient='records')
        total_dict = df_unique_dict
        result_df = result
    else:
        df_unique,final_df,usage_df,tmp_df = process_all(pdf_path)
        df_unique['account_number'] = acc_info
        final_df['account_number'] = acc_info
        df_unique_dict = df_unique.to_dict(orient='records')
        total_dict = df_unique_dict
        result_df = final_df
    for entry in total_dict:
        entry['company'] = company_nm
        entry['vendor'] = vendor_nm
        entry['sub_company'] = sub_com

        entry['location'] = location

        if isinstance(bill_date, list):
            entry['bill_date'] = bill_date[0]
        else:
            entry['bill_date'] = bill_date
    res_data_dict = result_df.to_dict(orient='records')
    for entry in res_data_dict:
        entry['company'] = company_nm
        entry['vendor'] = vendor_nm
        entry['sub_company'] = sub_com
        entry['location'] = location
    return res_data_dict,total_dict,tmp_df


def save_to_unique_pdf_data_table(data,vendor,types, bill_path):
    
    data_df = pd.DataFrame(data)
    if 'mobile' in str(vendor).lower() and check_tmobile_type(bill_path) == 1:
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
    elif 'mobile' in str(vendor).lower() and check_tmobile_type(bill_path) == 2:
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
        data_df.drop(columns=['Page Number','Monthly charges Add-ons','Billing_Name','Billing_Address', 'Remidence_Addresss','Activity since last bill'],inplace=True)
    data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account Number':'account_number_y','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
    data_df.columns = data_df.columns.str.replace('&', 'and')
    data_df.columns = data_df.columns.str.replace('-', ' ')
    data_df.columns = data_df.columns.str.replace(' ', '_')
    data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
    data = data_df.to_dict(orient='records')
    from ..models import UniquePdfDataTable
    for item in data:
        UniquePdfDataTable.objects.create(**item)


def save_to_baseline_data_table(data,vendor,types):
    
    data_df = pd.DataFrame(data)
    if vendor in ['T_Mobile','t-mobile','T-mobile','t_mobile'] and types== 'first':
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
    elif vendor in ['T_Mobile','t-mobile','T-mobile','t_mobile'] and types== 'second':
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
        data_df.drop(columns=['Page Number','Monthly charges Add-ons','Billing_Name','Billing_Address', 'Remidence_Addresss','Activity since last bill'],inplace=True)
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
    from ..models import BaselineDataTable
    for item in data:
        for key, value in item.items():
            if isinstance(value, dict):
                item[key] = json.dumps(value)  # Convert dictionaries to JSON strings

        BaselineDataTable.objects.create(**item)



def save_to_pdf_data_table(data,vendor,types):
    
    data_df = pd.DataFrame(data)
    print('in saves B')
    print(data_df.columns)
    if vendor in ['T_Mobile','t-mobile','T-mobile','t_mobile'] and types=='first':
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
    elif vendor in ['T_Mobile','t-mobile','T-mobile','t_mobile'] and types=='second':
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
        data_df.drop(columns=['Page Number','Monthly charges Add-ons','Billing_Name','Billing_Address', 'Remidence_Addresss','Activity since last bill'],inplace=True)
    data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account_number':'Account_number','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
    data_df.columns = data_df.columns.str.replace('&', 'and')
    data_df.columns = data_df.columns.str.replace('-', ' ')
    data_df.columns = data_df.columns.str.replace(' ', '_')
    data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
    data = data_df.to_dict(orient='records')
    from ..models import PdfDataTable
    for item in data:
        PdfDataTable.objects.create(**item)


def save_to_base_data_table(data):
    from django.db import transaction
    from ..models import BaseDataTable
    try:
        with transaction.atomic():  # Ensures atomicity of the database operations
            for item in data:
                BaseDataTable.objects.create(**item)
    except:
        BaseDataTable.objects.create(**data)

def save_to_batch_report(data, vendor):
    try:
        at_vendor_list = ['AT&T', 'AT n T', 'ATT', 'at&t', 'att', 'at n t']
        if vendor in ['T_Mobile','t-mobile','T-mobile','t_mobile']:
            return None
        if vendor in at_vendor_list:
            temp = data
            temp_fig = data
        else:
            temp = data[0]
            temp_fig = data[0]

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
        if vendor in at_vendor_list:
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
        'Vendor_Zip': 'Vendor_Zip'
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
    from django.db import transaction
    from ..models import BatchReport
    existing_data = BatchReport.objects.filter(
        Customer_Vendor_Account_Number=renamed_data['Customer_Vendor_Account_Number'],
        company=renamed_data['company'],
        Vendor_Name_1=renamed_data['Vendor_Name_1'],
        Invoice_Date=renamed_data['Invoice_Date']
    ).first()

    try:
        batch_vendor = vendor
        at_vendor_list = ['AT&T', 'AT n T', 'ATT', 'at&t', 'att', 'at n t']
        ver_list = ['verizon', 'VERIZON', 'ver', 'VER', 'Verizon']
        if vendor in at_vendor_list:
            batch_vendor = 'ATT'
        elif vendor in ver_list:
            batch_vendor = 'VER'

        entered_vendor_zip = zip_code
        entered_vendor_state = state
        entered_vendor_city = city

        count_matches = BatchReport.objects.filter(
            Vendor_Zip=entered_vendor_zip,
            Vendor_State=entered_vendor_state,
            Vendor_City=entered_vendor_city
        ).count()

        if count_matches > 0:
            max_location_code = BatchReport.objects.filter(
                Vendor_Zip=entered_vendor_zip,
                Vendor_State=entered_vendor_state,
                Vendor_City=entered_vendor_city
            ).order_by('-Location_Code').values_list('Location_Code', flat=True).first()

            if max_location_code:
                max_number = int(max_location_code[3:])  # Extract numeric part
                new_location_code = f"{batch_vendor}{str(max_number + 1).zfill(3)}"
            else:
                new_location_code = f"{batch_vendor}001"

            BatchReport.objects.filter(
                Vendor_Zip=entered_vendor_zip,
                Vendor_State=entered_vendor_state,
                Vendor_City=entered_vendor_city
            ).update(Location_Code=new_location_code)

            print("Location code assigned/updated for the entered vendor-zip:", new_location_code)
        else:
            print("The entered vendor-zip number does not exist in the database.")
    except Exception as e:
        print("Error:", str(e))

    with transaction.atomic():
        if existing_data:
            existing_data.Due_Date = renamed_data['Due_Date']
            existing_data.Invoice_Number = renamed_data['Invoice_Number']
            existing_data.Invoice_Date = renamed_data['Invoice_Date']
            existing_data.Cust_Id = renamed_data['Cust_Id']
            existing_data.Net_Amount = renamed_data['Net_Amount']
            existing_data.save()
        else:
            new_entry = BatchReport.objects.create(**renamed_data)
            
            if 'new_location_code' in locals():
                new_entry.Location_Code = new_location_code
                new_entry.save()

def extract_rdd_data(file_path):
            extract_dir = './extracted_files'
            os.makedirs(extract_dir, exist_ok=True)

            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            except zipfile.BadZipFile:
                return "Error: Invalid zip file."
            except Exception as e:
                return f"Error: {str(e)}"
            
            def process_desired_file_1(file_path):
                with open(file_path, 'r') as file:
                    file_data = file.read()
                    df = pd.read_csv(StringIO(file_data), sep='\t')
                    def convert_column_name(column_name):
                        return column_name.lower().replace(' ', '_')
                    df.columns = df.columns.map(convert_column_name)
                    required_columns = ['bill_cycle_date', 'account_number', 'date_due',
                    'invoice_number', 'bill_period', 'wireless_number', 'user_name',
                    'cost_center', 'your_calling_plan',
                    'account_charges_and_credits', 'monthly_charges',
                    'usage_and_purchase_charges', 'equipment_charges',
                    'total_surcharges_and_other_charges_and_credits',
                    'taxes,_governmental_surcharges_and_fees', 'third_party_charges',
                    'total_charges','voice_plan_usage', 'messaging_usage']
                    required_df = df[required_columns].copy()
                    column_mapping = {
                        'bill_cycle_date': 'bill_date',
                        'bill_period': 'duration',
                        'your_calling_plan':'plans',
                        'invoice_number':'invoicenumber',
                        'account_number':'accountnumber',
                        "total_surcharges_and_other_charges_and_credits":"surcharges_and_other_charges_and_credits",
                        'taxes,_governmental_surcharges_and_fees':'taxes_governmental_surcharges_and_fees',
                        'third_party_charges':'third_party_charges_includes_tax'
                    }
                    required_df.rename(columns=column_mapping,inplace=True)
                    # conn = sqlite3.connect('db.sqlite3')
                    base_data_df = required_df.iloc[1][['bill_date', 'accountnumber', 'date_due',
                    'invoicenumber', 'duration','total_charges']].copy()
                    acc_mapping = {'accountnumber':'account_number'}
                    required_df.rename(columns=acc_mapping,inplace=True)
                    # base_data_df.to_sql('myapp_base_data_table',conn,if_exists='replace', index=False)
                    pdf_data_df = required_df[['account_number','wireless_number','user_name','plans','cost_center',
                    'account_charges_and_credits', 'monthly_charges',
                    'usage_and_purchase_charges', 'equipment_charges',
                    'surcharges_and_other_charges_and_credits',
                    'taxes_governmental_surcharges_and_fees', 'third_party_charges_includes_tax',
                    'total_charges','voice_plan_usage', 'messaging_usage']].copy()
                    # pdf_data_df.to_sql('myapp_pdf_data_table',conn,if_exists='replace', index=False)
                    # pdf_data_df.to_sql('myapp_unique_pdf_data_table',conn,if_exists='replace', index=False)
                    # conn.close()
                    return base_data_df,pdf_data_df

            def process_desired_file_2(file_path):
                with open(file_path, 'r') as file:
                    file_data = file.read()
                    df = pd.read_csv(StringIO(file_data), sep='\t')
                    df.rename(columns={'Cost':'Charges'},inplace=True)
                    detailed_df = df
                    return detailed_df
            def cleanup_extracted_files(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        os.remove(os.path.join(root, file))
                os.rmdir(directory)

            relevant_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file_name in files:
                    if file_name.endswith('.txt'):
                        relevant_files.append(os.path.join(root, file_name))
            
            for file_path in relevant_files:
                if 'Account & Wireless Summary' in file_path:                    
                    data_base,data_pdf = process_desired_file_1(file_path)
                    data_base_dict = data_base.to_dict()
                    data_pdf_dict = data_pdf.to_dict(orient='records')
                elif 'Acct & Wireless Charges Detail Summary' in file_path:
                    detailed_df = process_desired_file_2(file_path)


            cleanup_extracted_files(extract_dir)

            return data_base_dict,data_pdf_dict,detailed_df

def save_user_pdf(acc_no, bill_date, pdf_path):
    from ..models import UserPDF
    UserPDF.objects.create(acc_no=acc_no, bill_date=bill_date, pdf=pdf_path)


def process_pdf_from_buffer(buffer_data):
    pdf_path = buffer_data['pdf_path']
    company_name = buffer_data['company_name']
    vendor_name = buffer_data['vendor_name']
    pdf_filename = buffer_data['pdf_filename']
    month = buffer_data['month']
    entry_type = buffer_data['entry_type']
    baseline_check = buffer_data['baseline_check']

    location = buffer_data['location']
    master_account = buffer_data['master_account']

    year = buffer_data['year']
    types = buffer_data['types']
    # email = buffer_data['email']
    sub_company = buffer_data['sub_company']
    logger.info(f'Processing PDF from buffer: {pdf_path}, {company_name}, {vendor_name}, {pdf_filename}')

    if 'mobile' in str(vendor_name).lower():
        check_type = check_tmobile_type(Billpath=pdf_path)
        global t_mobile_type
        if check_type == 1:
            t_mobile_type = 1
        elif check_type == 2:
            t_mobile_type = 2
        else:
            t_mobile_type = 0
    check = True
    if check:
            
        logger.info('Extracting data from PDF')
        try:    

            data, acc_info, bill_date_info = extract_data_from_pdf(pdf_path, company_name, vendor_name, pdf_filename,month,year,sub_company,types,entry_type,location,master_account)
            

            save_to_base_data_table(data)
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
            print("*********",pdf_path, acc_info, company_name, vendor_name,bill_date_info,sub_company)
            print('rex')
            pdf_data, unique_pdf_data,tmp_df = extract_total_pdf_data(pdf_path, acc_info, company_name, vendor_name,bill_date_info,sub_company,types,location)
            print('brock')
            dir = 'output'
            # i = pd.DataFrame(pdf_data)
            # filename = 't_mobile_category.csv'
            # path = os.path.join(dir,filename)
            # tmp_df.to_csv(path)
            wireless_data = defaultdict(lambda: defaultdict(dict))
            if vendor_name in ['T_Mobile','t-mobile','T-mobile','t_mobile'] and types == 'first':
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
            save_to_pdf_data_table(pdf_data,vendor_name,types)
            print('got here')
            save_to_unique_pdf_data_table(unique_pdf_data,vendor_name,types, pdf_path)
            if month == None and year == None:
                print("**",type(baseline_check))
                if baseline_check == 'false': 
                    baseline_check = False
                if baseline_check:
                    save_to_baseline_data_table(category_data,vendor_name,types)
                else:
                    save_to_baseline_data_table(non_categorical_data,vendor_name,types)    
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

