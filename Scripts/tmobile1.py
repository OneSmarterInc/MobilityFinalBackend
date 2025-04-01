import pdfplumber
import re,os
import pandas as pd

def extract_data_tmobile_type_1(t_mobile_filename):
    def extract_text_from_t_mobile(filename):
        with pdfplumber.open(filename) as pdf:
            pages_data = [page.extract_text() for page in pdf.pages]
        text = '\n'.join(pages_data)
        lines = text.strip().split("\n")
        data_list = []
        wireless_number_pattern = re.compile(r"Subscriber Service Detail for \((\d{3})\) (\d{3})-(\d{4})")
        data_usage_pattern = re.compile(r"Mobile Internet Gigabytes - ([\d\.]+) ([\d\.]+) ([\d\.]+)")
        current_number = None
        for line in lines:
            wireless_match = wireless_number_pattern.search(line)
            data_usage_match = data_usage_pattern.search(line)
            if wireless_match:
                current_number = f"{wireless_match.group(1)}-{wireless_match.group(2)}-{wireless_match.group(3)}"
            
            if data_usage_match and current_number:
                data_usage = [float(data_usage_match.group(i)) for i in range(1, 4)]
                data_dict = {
                    "wireless number": current_number,
                    "Data Usage": sum(data_usage)
                }
                data_list.append(data_dict)
        usage_df = pd.DataFrame(data_list)
        return text,usage_df

    def extract_first_page_t_mobile_data(filename):
        with pdfplumber.open(filename) as pdf:
            pages_data = [page.extract_text() for page in pdf.pages[:1]]
        text = '\n'.join(pages_data)
        lines = text.strip().split("\n")
        summary_dict = {}
        vendor_address = 'T-MOBILE PO BOX 742596 CINCINNATI OH 45274-2596'
        billing_name_pattern = re.compile(r'Statement For:\s*(.*)')
        account_number_pattern = re.compile(r'Account Number:\s*([\d\s]+)')
        complete_address_pattern = r'(?<=SOUTHERNCARLSON INC\n)(\d+\s+.+?\d{5}-\d{4})'
        complete_address_match = re.search(complete_address_pattern, text, re.DOTALL)
        try:
            complete_address = complete_address_match.group(1).strip()
        except:
            complete_address = ''
        field_patterns = {
            'Previous Balance': re.compile(r'Previous Balance\s*\$ ([\d,]+\.\d{2})'),
            'Payment Received': re.compile(r'Pmt Rec�d - Thank You\s*\$ \(([\d,]+\.\d{2})\)'),
            'Total Past Due': re.compile(r'Total Past Due\s*\$ \(([\d,]+\.\d{2})\)\s*\(Credit Balance\)'),
            'Monthly Recurring Charges': re.compile(r'Monthly Recurring Chgs\s*\$ ([\d,]+\.\d{2})'),
            'Credits & Adjustments': re.compile(r'Credits & Adjustments\s*\$ \(([\d,]+\.\d{2})\)'),
            'Usage Charges': re.compile(r'Usage Charges\s*\$ ([\d,]+\.\d{2})'),
            'One Time Charges': re.compile(r'One Time Charges\s*\$ ([\d,]+\.\d{2})'),
            'Other Charges': re.compile(r'Other Charges\s*\$ ([\d,]+\.\d{2})'),
            'Taxes & Surcharges': re.compile(r'Taxes & Surcharges\s*\$ ([\d,]+\.\d{2})'),
            'Total Current Charges': re.compile(r'Total Current Charges\s*\$ ([\d,]+\.\d{2})'),
            'Grand Total': re.compile(r'Grand Total\s*\$ ([\d,]+\.\d{2})')
        }
        
        current_address_lines = []
        capture_address = False

        for line in lines:
            if billing_name_match := billing_name_pattern.search(line):
                summary_dict['Billing Name'] = billing_name_match.group(1)
            elif account_number_match := account_number_pattern.search(line):
                summary_dict['Account Number'] = account_number_match.group(1).replace(' ', '')
            elif 'your bill on time' in line:
                capture_address = False
                if current_address_lines:
                    summary_dict['Address'] = ' '.join(current_address_lines).strip()
                    current_address_lines = []
            elif 'Statement For:' in line:
                capture_address = True
            elif capture_address:
                current_address_lines.append(line.strip())
            
            for field, pattern in field_patterns.items():
                if match := pattern.search(line):
                    summary_dict[field] = match.group(1).replace(',', '')
        summary_dict['Address'] = complete_address
        summary_dict['Vendor_Address'] = vendor_address
        return summary_dict


    def parse_billing_info(text):
        lines = text.strip().split("\n")
        parsed_data = {}
        plan_data = {}
        keys = ['Statement For', 'Account Number', 'Customer Service Number', 'Monthly service charges from']
        statement_info = {}
        data = {}
        data_list = []
        capture_monthly_charge = False
        current_mobile_number = None
        mobile_regex = re.compile(r'(\d{3}-\d{3}-\d{4}) (.+?) - Balance of Remaining Payments\* \$([0-9,.]+)')
        monthly_charge_regex = re.compile(r'Monthly Charge \$([0-9,.]+)')

        next_parsed_data = {
            'account number': '',
            'date':'',
            'wireless number': [],
            'address': '',
            'item category': [],
            'item description': [],
            'charges': [],
            'data': [],
            'minutes': [],
            'messages': []
        }
        plan_regex = re.compile(r'Plan #(\d+) - Balance of Remaining Payments\* \$([0-9,.]+)')
        mobile_regex = re.compile(r'(\d{3}-\d{3}-\d{4}) (.+?) - Balance of Remaining Payments\* \$([0-9,.]+)')
        final_charge_regex = re.compile(r'Final Charge\*\* \$([0-9,.]+)')
        monthly_charge_regex = re.compile(r'Monthly Charge \$([0-9,.]+)')
        account_number_pattern = re.compile(r'Account Number:\s*(\d+)')
        customer_service_pattern = re.compile(r'Customer Service Number\s*(\S+)')
        address_pattern = re.compile(r'A d d r e s s a t w h i c h t h i s l i n e is primarily used:\s*(.*)')
        mobile_number_pattern = re.compile(r'Subscriber Service Detail for\s*\((\d{3})\)\s*(\d{3})-(\d{4})')
        address_next_line = False
        capture_address = False
        capture_data_plan_next_line = False
        current_mobile_number = None
        current_plan = None
        in_available_services = False
        in_used_services = False
        in_charges_section = False
        for i in range(len(lines)):
            mo_ch = 0
            fo_ch = 0
            for key in keys:
                if key in lines[i]:
                    value = lines[i].split(key)[-1].strip()
                    statement_info[key] = value
            if "$" in lines[i] and '-' in lines[i]:
                parts = lines[i].split('$')
                if len(parts) > 6:
                    mobile_number = parts[0]
                    charges = parts[1:]
                    parsed_data[mobile_number] = {
                        "Recurring Charges": charges[0].strip().replace(",", "") if charges[0].strip() else 0,
                        "Adjustments": charges[1].strip().replace(",", "") if charges[1].strip() else 0,
                        "Usage Charges":charges[2].strip().replace(",", "") if charges[2].strip() else 0,
                        "One Time Charges": charges[3].strip().replace(",", "") if charges[3].strip() else 0,
                        "Other Charges": charges[4].strip().replace(",", "") if charges[4].strip() else 0,
                        "Third-party Charges": charges[5].strip().replace(",", "") if charges[5].strip() else 0,
                        "Taxes & Surcharges": charges[6].strip().replace(",", "") if charges[6].strip() else 0,
                        "Total Current Charges": charges[7].strip().replace(",", "") if charges[7].strip() else 0
                    }

            plan_match = plan_regex.match(lines[i])
            if plan_match:
                current_plan = plan_match.group(1)
                continue
            # Match mobile number and device details
            mobile_match = mobile_regex.match(lines[i])
            if mobile_match:
                mobile_number = mobile_match.group(1).replace("-", "")
                device_model = mobile_match.group(2).strip()
                balance_remaining = mobile_match.group(3)
                try:
                    if 'Monthly Charge' in lines[i+1]:
                        mo_ch = lines[i+1][-6:]
                    elif 'Final Charge' in lines[i+1]:
                        fo_ch = lines[i+1][-6:]
                except:
                    pass
                plan_data[mobile_number] = {
                    'Plan': current_plan,
                    'Device Model': device_model,
                    'Balance of Remaining Payments': balance_remaining,
                    'Final Charge': fo_ch,
                    'Monthly Charge': mo_ch
                }
                continue
            # if capture_monthly_charge:
            #     print('into it')
            # # Capture the monthly charge from the next line
            #     monthly_charge_match = monthly_charge_regex.match(line)
            #     print(line)
            #     print(monthly_charge_match)
            #     if monthly_charge_match and mobile_number:
            #         monthly_charge = monthly_charge_match.group(1)
            #         print(monthly_charge)
            #         plan_data[mobile_number]['Monthly Charge'] = monthly_charge
            #         capture_monthly_charge = False  # Reset flag after capturing the charge
            # else:
            #     print('not in')
            # # Match final charge
            # final_charge_match = final_charge_regex.search(line)
            # if final_charge_match and mobile_number in plan_data:
            #     final_charge = final_charge_match.group(1)
            #     plan_data[mobile_number]['Final Charge'] = final_charge
            #     continue

            # monthly_charge_match = monthly_charge_regex.search(line)
            # if monthly_charge_match and mobile_number in plan_data:
            #     monthly_charge = monthly_charge_match.group(1)
            #     plan_data[mobile_number]['Monthly Charge'] = monthly_charge
            line = lines[i]
            if account_number_match := account_number_pattern.search(line):
                data['Account Number'] = account_number_match.group(1)
            elif customer_service_match := customer_service_pattern.search(line):
                data['Customer Service Number'] = customer_service_match.group(1)
            elif mobile_number_match := mobile_number_pattern.search(line):
                current_mobile_number = f"({mobile_number_match.group(1)}) {mobile_number_match.group(2)}-{mobile_number_match.group(3)}"
                if 'Mobile Numbers' not in data:
                    data['Mobile Numbers'] = {}
                data['Mobile Numbers'][current_mobile_number] = {}
            elif 'A d d r e s s a t w h i c h t h i s l i n e is primarily used:' in line:
                address_next_line = True
            elif address_next_line:
                if current_mobile_number:
                    data['Mobile Numbers'][current_mobile_number]['Address'] = line.strip()
                address_next_line = False
            elif 'Available Service Type' in line:
                capture_data_plan_next_line = True
            elif capture_data_plan_next_line:
                if current_mobile_number:
                    data['Mobile Numbers'][current_mobile_number]['Data Plan'] = line.strip()
                capture_data_plan_next_line = False

            line = line.strip()
            if line.startswith('Account Number:'):
                next_parsed_data['account number'] = line.split(': ')[1]
            elif 'Page' in line and 'o f' in line:
                next_parsed_data['date'] = ' '.join(line.split()[0:3])
            elif 'Page' in line and 'of' in line:
                next_parsed_data['date'] = ' '.join(line.split()[0:3])
            elif 'Itemized Details For' in line:
                current_wireless_number = line.split(': ')[1]
            elif 'Subscriber Service Detail for' in line:
                current_wireless_number = line.split('(')[1].split(')')
            elif 'Addressatwhichthis line is primarily used:' in line:
                in_address = True
            elif 'A d d r e s s a t w h i c h t h i s l i n e is primarily used:' in line :
                in_address = True
            elif 'Available Service Type' in line:
                in_available_services = True
                in_used_services = False
                in_charges_section = False
            elif 'Used Service Type' in line:
                in_available_services = False
                in_used_services = True
                in_charges_section = False
            elif 'Monthly Recurring Charges' in line:
                in_available_services = False
                in_used_services = False
                in_charges_section = True
            elif in_available_services:
                if line:
                    next_parsed_data['item category'].append('available services')
                    next_parsed_data['item description'].append(line)
                    next_parsed_data['charges'].append('-')
                    next_parsed_data['data'].append('')
                    next_parsed_data['minutes'].append('')
                    next_parsed_data['messages'].append('')
                    next_parsed_data['wireless number'].append(locals().get('current_wireless_number', '000-000-0000'))
            elif in_used_services:
                if line:
                    next_parsed_data['item category'].append('used services')
                    next_parsed_data['item description'].append(line)
                    next_parsed_data['charges'].append('-')
                    # Extracting minutes and data if available
                    if 'Minutes' in line:
                        try:
                            next_parsed_data['minutes'].append(line.split('Minutes - ')[1].split(' ')[0])
                        except:
                            next_parsed_data['minutes'].append(line.split('Minutes')[-1].strip().split()[0])
                        next_parsed_data['data'].append('')
                        next_parsed_data['messages'].append('')
                    elif 'Gigabytes' in line:
                        try:
                            next_parsed_data['data'].append(line.split('Gigabytes - ')[1].split(' ')[0])
                        except:
                            try:
                                next_parsed_data['data'].append(line.split('Gigabytes - ')[1].split(' ')[0])
                            except:
                                try:
                                    next_parsed_data['data'].append(line.split('Gigabytes')[1].split(' ')[0])
                                except:
                                    next_parsed_data['data'].append('NA')
                        next_parsed_data['minutes'].append('')
                        next_parsed_data['messages'].append('')
                    else:
                        next_parsed_data['data'].append('')
                        next_parsed_data['minutes'].append('')
                        next_parsed_data['messages'].append('')
                    next_parsed_data['wireless number'].append(locals().get('current_wireless_number', '000-000-0000'))
            if line and '$' in line:
                    description, charge = line.rsplit('$', 1)
                    next_parsed_data['item category'].append('charges')
                    next_parsed_data['item description'].append(description.strip())
                    next_parsed_data['charges'].append(charge.strip())
                    next_parsed_data['data'].append('')
                    next_parsed_data['minutes'].append('')
                    next_parsed_data['messages'].append('')
                    next_parsed_data['wireless number'].append(locals().get('current_wireless_number', '000-000-0000'))

        # Address parsing
        try:
            try:
                address_start = lines.index('A d d r e s s a t w h i c h t h i s l i n e is primarily used:') + 1
            except:
                address_start = lines.index('Addressatwhichthis line is primarily used:') + 1
            address_end = address_start + 2
            next_parsed_data['address'] = '\n'.join(lines[address_start:address_end])
        except:
            next_parsed_data['address'] = 'NA'
        # Date parsing
        # for line in lines:
        #     if 'Page' in line and 'of' in line:
        #         next_parsed_data['date'] = ' '.join(line.split()[-4:-1])+
        # Create DataFrame
        next_df = pd.DataFrame({
            'account number': [next_parsed_data['account number']] * len(next_parsed_data['item category']),
            'wireless number': next_parsed_data['wireless number'],
            'address': [next_parsed_data['address']] * len(next_parsed_data['item category']),
            'item category': next_parsed_data['item category'],
            'item description': next_parsed_data['item description'],
            'charges': next_parsed_data['charges'],
            'data': next_parsed_data['data'],
            'minutes': next_parsed_data['minutes'],
            'messages': next_parsed_data['messages'],
            'date': [next_parsed_data['date']] * len(next_parsed_data['item category'])
        })


        return parsed_data,statement_info,plan_data,data,next_df

    file = t_mobile_filename
    summary = extract_first_page_t_mobile_data(file)
    text,usage_df = extract_text_from_t_mobile(file)
    gtr,rtr,mtr,dtr,next_df = parse_billing_info(text)
    gtr_df = pd.DataFrame.from_dict(gtr, orient='index')
    gtr_df.index.name = 'Wireless Number'
    gtr_df.reset_index(inplace=True)
    flat_data = []
    for number, details in dtr['Mobile Numbers'].items():
        keys = list(details.keys())
        try:
            address_data = details[keys[1]]
        except:
            address_data = ''
        try:
            data_plan = details[keys[0]]
        except:
            data_plan = ''
        flat_data.append({'Account Number': dtr['Account Number'],
                        'Customer Service Number': dtr['Customer Service Number'],
                        'Mobile Number': number,
                        'Data Plan': data_plan,
                        'Address': address_data})
    dtr_df = pd.DataFrame(flat_data)
    mtr_df = pd.DataFrame.from_dict(mtr, orient='index')
    mtr_df.index.name = 'Wireless Number'
    mtr_df.reset_index(inplace=True)
    summary_df = pd.DataFrame([summary])
    rtr_df = pd.DataFrame([rtr])
    dtr_df = dtr_df.rename(columns={'Mobile Number':'Wireless Number'})
    dtr_df['Wireless Number'] = dtr_df['Wireless Number'].str.replace(r'[() ]', lambda x: '-' if x.group(0) == ' ' else '', regex=True)
    def format_phone_number(phone_number):
        cleaned_number = ''.join(filter(str.isdigit, phone_number))
        if len(cleaned_number) != 10:
            return "Invalid phone number"
        formatted_number = cleaned_number[:3] + '-' + cleaned_number[3:6] + '-' + cleaned_number[6:]
        return formatted_number
    mtr_df['Wireless Number'] = mtr_df['Wireless Number'].apply(format_phone_number)
    temp_gtr = gtr_df
    gtr_df = gtr_df.drop(index=0)
    gtr_df['Wireless Number'] = gtr_df['Wireless Number'].str.replace(' ','')
    rtr_df['Account Number'] = rtr_df['Account Number'].str.replace(':','').str.replace(' ','')
    summary_df['Account Number'] = summary_df['Account Number'].str.replace(' ','')
    merged_df_base_data = pd.merge(summary_df,rtr_df,on='Account Number',how='inner')
    merged_df_temp_data = pd.merge(dtr_df,gtr_df,on='Wireless Number',how='inner')
    merged_df_total_data = pd.merge(merged_df_temp_data,mtr_df,on='Wireless Number',how='inner')
    # output_dir = 'output_files'
    # os.makedirs(output_dir, exist_ok=True)
    # summary_df.to_csv(f'{output_dir}/summary.csv', index=False)
        # gtr_df.to_csv(f'{output_dir}/gtr.csv', index=False)
    # rtr_df.to_csv(f'{output_dir}/rtr.csv', index=False)
    # mtr_df.to_csv(f'{output_dir}/mtr.csv', index=False)
    # dtr_df.to_csv(f'{output_dir}/dtr.csv', index=False)
    # merged_df_base_data.to_csv(f'{output_dir}/base_data.csv', index=False)
    # merged_df_total_data.to_csv(f'{output_dir}/total_data.csv', index=False)
    # merged_df_temp_data.to_csv(f'{output_dir}/detailed_data.csv',index=False)
    return temp_gtr,merged_df_base_data,merged_df_total_data,merged_df_temp_data,next_df,dtr_df,mtr_df,summary_df,usage_df

import zipfile
import os
import shutil
def zip_folder(folder_path):
    output_zip = f'{folder_path}.zip'

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)  # Keep relative paths
                zipf.write(file_path, arcname)
    return os.path.relpath(output_zip)
def get_all_dataframes_type_1(file):
    gtr_df,merged_df_base_data,merged_df_total_data,merged_df_temp_data,next_df,dtr_req,mmt,summer,usage= extract_data_tmobile_type_1(file)
    
    unique_date = next_df['date'].unique()[0]
    unique_account_number = next_df['account number'].unique()[0]
    def format_wireless_number(parts):
        area_code = parts[0].strip()
        first_part, second_part = parts[1].strip().split('-')
        return f"{area_code}-{first_part}-{second_part}"
    next_df.replace('', 'NA', inplace=True)
    try:
        next_df['wireless number'] = next_df['wireless number'].apply(format_wireless_number)
    except:
        next_df['wireless number'] = next_df['wireless number']

    filtered_df = next_df[~next_df['item description'].isin(['Other Charges', 'Government Taxes and Fees & T-Mobile Fees and Charges','Monthly Recurring Charges'])]
    fffiltered_df = next_df[next_df['item description'] == 'Total Charges']
    new_dfra  = fffiltered_df[['item description', 'charges']]
    filtered_df = filtered_df[filtered_df['wireless number'] != '000-000-0000']
    def convert_to_positive(value):
        try:
            # Attempt to convert to float and take the absolute value
            return str(abs(float(value)))
        except ValueError:
            # If conversion fails (non-numeric value), return '0'
            return '0'
    filtered_df['charges'] = filtered_df['charges'].apply(convert_to_positive)
    gtr_df.rename(columns={'Wireless Number':'wireless number'},inplace=True)
    def format_number(number):
        if isinstance(number, str):
            number = number.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')
            number = number.replace('[', '').replace(']', '').replace("'", '').replace(',', '')
            number = number.replace('{', '').replace('}', '').replace(' ', '').replace('-', '')
            if len(number) == 10:
                return f'{number[:3]}-{number[3:6]}-{number[6:]}'
        return number

    # Applying the function to the wireless number column
    def list_to_string(lst):
        return f'{lst[0]}-{lst[1].strip()}'
    
    excelname = str(file).split('/')[-1].replace('.pdf', '')
    output_dir = excelname
    os.makedirs(output_dir, exist_ok=True)
    filtered_df['wireless number'] = filtered_df['wireless number'].apply(list_to_string)
    filtered_df['wireless number'] = filtered_df['wireless number'].apply(format_number)
    gtr_df['wireless number'] = gtr_df['wireless number'].apply(format_number)
    filtered_df.to_csv(f'{output_dir}/{excelname}_gottrew.csv', index=False)
    gtr_df.to_csv(f'{output_dir}/ {excelname}_got2.csv', index=False)
    dtr_req.rename(columns={'Wireless Number':'wireless number'},inplace=True)
    semi_final_merged_df = pd.merge(filtered_df,gtr_df,on='wireless number',how='inner')
    final_merged_df = pd.merge(semi_final_merged_df,dtr_req,on='wireless number',how='inner')
    mmt['Monthly Charge'] = mmt['Monthly Charge'].str.replace('$','').astype(float)
    mmt.rename(columns={'Wireless Number':'wireless number','Monthly Charge':'charges'},inplace=True)
    mmt_new = mmt[['wireless number','charges']]
    result_df = pd.concat([final_merged_df,mmt_new],ignore_index=True)
    final_merged_df = result_df
    # final_merged_df = final_merged_df[final_merged_df['item description'] != 'Total Charges']
    final_merged_df = final_merged_df[final_merged_df['item description'] != 'O t h e r C h a r g e s']
    first_merged_df = gtr_df
    columns_to_add = [
        'Data Usage (KB)', 
        'Data Usage (MB)', 
        'Voice Roaming', 
        'Messaging Roaming', 
        'Data Roaming (KB)', 
        'Data Roaming (MB)', 
        'Data Roaming (GB)'
    ]

    # Add the columns with default value 0
    for column in columns_to_add:
        final_merged_df[column] = 0
        first_merged_df[column] = 0
    empty_columns = [
        'User name',
        'Invoice number',
        'ECPD Profile',
        'User ID',
        'Foundation account'
    ]

    new_first_row = pd.DataFrame({
        'wireless number': ['Account charges'],
        'Total Current Charges': [0]
    })
    new_row = pd.DataFrame({
        'wireless number': ['Account charges'],
        'charges': [0]
    })

    for col in empty_columns:
        final_merged_df[col] = ''
        first_merged_df[col] = ''
    first_merged_df['item category'] = 'Monthly Charges'
    first_merged_df['item description'] = dtr_req['Data Plan']
    first_merged_df['bill_date'] = final_merged_df['date'].iloc[0]
    final_merged_df = final_merged_df.replace('NA', '')
    final_merged_df = pd.concat([new_row, final_merged_df], ignore_index=True)
    # first_merged_df = pd.concat([new_first_row, first_merged_df], ignore_index=True)
    charges_columns = ['Total Current Charges']
    first_row_charges = gtr_df.loc[0, charges_columns]
    charges = ['charges']
    final_merged_df.loc[0, charges] = first_row_charges.values
    final_merged_df = final_merged_df[final_merged_df['item description'] != 'One Time Charges']
    # first_merged_df.loc[0, charges_columns] = first_row_charges.values
    def process_charges(df):
    # Create output directory
        # output_dir = 'output_test_dir'
        # os.makedirs(output_dir, exist_ok=True)
        
        # Initialize DataFrame to store discrepancies
        discrepancies = pd.DataFrame(columns=df.columns)
        
        # Iterate through the DataFrame by wireless number
        unique_numbers = df['wireless number'].unique()
        
        for number in unique_numbers:
            subset = df[df['wireless number'] == number]
            
            # Calculate total charges from individual charges
            charges_sum = 0
            total_charges_row = None
            for index, row in subset.iterrows():
                if row['item description'] == 'Total Charges':
                    total_charges_row = row
                    break  # Once 'Total Charges' row is found, break the loop
                try:
                    charges_sum += float(row['charges'])
                except ValueError:
                    continue
            
            # Compare the calculated sum with the total charges
            charges_sum = round(charges_sum, 2)
            if total_charges_row is not None and charges_sum != float(total_charges_row['charges']):
                valid_rows = subset.dropna(subset=['item description', 'account number', 'item category'], how='all')
                discrepancies = pd.concat([discrepancies, valid_rows])
                # discrepancies = pd.concat([discrepancies, subset])
        
        # Save discrepancies to a separate Excel sheet
        descrepancies_cleaned = discrepancies[(discrepancies['item category'] != None) & (discrepancies['item description'] != None)]
        return descrepancies_cleaned
    
    
    descrepancies = process_charges(final_merged_df)
    final_merged_df = final_merged_df[final_merged_df['item description'] != 'Total Charges']
    final_merged_df.to_csv(f'{output_dir}/ {excelname}_DETAILED_new.csv', index=False)
    first_merged_df.to_csv(f'{output_dir}/ {excelname}_SUMMARY_new.csv', index=False)
    descrepancies.to_csv(f'{output_dir}/ {excelname}_Faultyxyxzzz_news.csv',index=False)
    merged_df_temp_data.to_csv(f'{output_dir}/{excelname}_detailed_data_.csv',index=False)
    merged_df_base_data.to_csv(f'{output_dir}/{excelname}_base_data_.csv', index=False)
    merged_df_total_data.to_csv(f'{output_dir}/{excelname}_total_data_.csv', index=False)

    zippath =zip_folder(output_dir)

    shutil.rmtree(output_dir)

    return summer,first_merged_df,final_merged_df,descrepancies,usage,unique_date,unique_account_number

# path = "Bills/Analysis/Scripts/oct-Tmob.pdf"
# obj = get_all_dataframes_type_1(path)