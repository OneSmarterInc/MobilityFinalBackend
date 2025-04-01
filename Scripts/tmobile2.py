import os
import re
import pandas as pd
import pdfplumber
import zipfile

def zip_folder(folder_path):
    output_zip = f'{folder_path}.zip'

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)  
                zipf.write(file_path, arcname)
    return os.path.relpath(output_zip)

def extract_text_from_t_mobile_2(filename):
    def find_pattern_on_page(page, pattern):
        # Search for the pattern in the text of the given page
        matches = re.findall(pattern, page.extract_text())
        return len(matches) > 0

    def extract_text_by_position(file_path, pattern):
        data = ''
        pattern_found = False

        with pdfplumber.open(file_path) as pdf:
            for page_num in range(len(pdf.pages)):
                page = pdf.pages[page_num]
                
                width = page.width

                # Check if the pattern has been found on this page
                if not pattern_found and find_pattern_on_page(page, pattern):
                    pattern_found = True

                if pattern_found:
                    left_half = page.crop((0, 0, width/2, page.height))
                    right_half = page.crop((width/2, 0, width, page.height))

                    data += '\n' + left_half.extract_text()
                    data += '\n' + right_half.extract_text()
                else:
                    # If pattern not found, just append the entire page's text
                    data += '\n' + page.extract_text()

        return data

    # Define the regular expression pattern to find
    pattern_to_find = r"\((\d{3})\) (\d{3}-\d{4}) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+)"

    data = extract_text_by_position(filename, pattern_to_find)
    wireless_number_pattern = re.compile(r'\((\d{3})\) (\d{3})-(\d{4}) \$(\d+\.\d{2})\n([^\n]+)')
    plan_pattern = r"PLANS -\n(.*?)\n(.*?)\n(.*?)\n"
    # Find all wireless numbers and plans
    wireless_numbers = re.findall(wireless_number_pattern, data)
    plans = re.findall(plan_pattern, data)
    plans_data = []
    for m in plans:
        plans_data.append(m[-1])
    phone_numbers = []
    for match in wireless_numbers:
        phone_number = f"({match[0]}) {match[1]}-{match[2]}"
        phone_numbers.append(phone_number)
    wireless_length = len(phone_numbers)
    if len(plans_data) == 0:
        for i in range(wireless_length):
            plans_data.append('NA')
    dataaa = {
        "Wireless Number": phone_numbers,
        "Plan": plans_data
    }
    df_temp = pd.DataFrame(dataaa)
    Lines = []
    lines = data.split('\n')
    for i, line in enumerate(lines):
        due_pattern = r"PREVIOUS TOTAL DUE \$(\d+\.\d{2})"
        payment_pattern = r"PAYMENTS (-?\$\d+\.\d{2})"
        matchss = re.search(due_pattern,line)
        payment_match = re.search(payment_pattern,line)
        if matchss:
            previous_total_due = matchss.group(1)
            Lines.append({'Wireless Number': 'Previuos Bill Charges', 'User Name': 'NA' , 'Plans': 'NA', 'Usage charges': 'NA', 'Equipment': 'NA', 'Services': 'NA', 'One-time charges': 'NA', 'Taxes & Fees': 'NA', 'Total': previous_total_due})
        if payment_match:
            payment = payment_match.group(1)
            Lines.append({'Wireless Number': 'Payments', 'User Name': 'NA' , 'Plans': 'NA', 'Usage charges': 'NA', 'Equipment': 'NA', 'Services': 'NA', 'One-time charges': 'NA', 'Taxes & Fees': 'NA', 'Total': payment})
        match = re.search(r"\((\d{3})\) (\d{3}-\d{4}) (.*?) p\.(\d+) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\-) (.*?) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+)", line)
        if match:
            Lines.append({'Wireless Number': 'NA' if match.group(1)+' '+match.group(2) == '-' else match.group(1)+' '+match.group(2), 'User Name': 'NA' if match.group(3) == '-' else match.group(3), 'Plans': 'NA' if match.group(5) == '-' else match.group(5), 'Usage charges': 'NA' if match.group(6).split()[0] == '-' else match.group(6).split()[0], 'Equipment': 'NA' if match.group(6).split()[1] == '-' else match.group(6).split()[1], 'Services': 'NA' if match.group(6).split()[2] == '-' else match.group(6).split()[2], 'One-time charges': 'NA' if match.group(6).split()[3] == '-' else match.group(6).split()[3], 'Taxes & Fees': 'NA' if match.group(7) == '-' else match.group(7), 'Total': 'NA' if match.group(8) == '-' else match.group(8)})
        else:
            match = re.search(r"(Account charges) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\-) (.*?) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+)", line)
            if match:
                Lines.append({'Wireless Number': 'NA', 'User Name': 'NA' if match.group(1) == '-' else match.group(1), 'Plans': 'NA' if match.group(2) == '-' else match.group(2), 'Usage charges': 'NA' if match.group(3).split()[0] == '-' else match.group(3).split()[0], 'Equipment': 'NA' if match.group(3).split()[1] == '-' else match.group(3).split()[1], 'Services': 'NA' if match.group(3).split()[2] == '-' else match.group(3).split()[2], 'One-time charges': 'NA' if match.group(3).split()[3] == '-' else match.group(3).split()[3], 'Taxes & Fees': 'NA' if match.group(4) == '-' else match.group(4), 'Total': 'NA' if match.group(5) == '-' else match.group(5)})

    import shutil
    df = pd.DataFrame(Lines)
    excelname = str(filename).split('/')[-1].replace('.pdf', '')
    unique_df = df
    df = df.drop(df.index[0])
    df['Wireless Number'] = df['Wireless Number'].str.replace(' ', '').str.replace('-', '')
    df_temp['Wireless Number'] = df_temp['Wireless Number'].str.replace('(', '').str.replace(')', '').str.replace(' ', '').str.replace('-', '')
    merged_df = pd.merge(df_temp, df, on="Wireless Number", how="inner")
    df = merged_df
    output_directory = excelname
    os.makedirs(output_directory, exist_ok=True)
    # file_path = os.path.join(output_directory, 'TMobiles_Bills_Details4.csv')
    # df.to_csv(file_path, index=False)
    df.to_csv(f'{output_directory}/{excelname}_summary.csv', index=False)
    df['Plans'] = df['Plans'].str.replace('$', '').str.replace('NA', '0').astype(float)
    df['Taxes & Fees'] = df['Taxes & Fees'].str.replace('$', '').str.replace('NA', '0').astype(float)
    df['Total'] = df['Total'].str.replace('$', '').str.replace('NA', '0').astype(float)
    lines = data.split('\n')
    result = []
    current_section = None
    check = 0
    voice_line = 0
    if 'previous_total_due' in locals():
        result.append({'Account Number': 'NA', 'Wireless Number': 'NA', 'User Name': 'NA', 'Connection Type': 'NA', 'Address': 'NA', 'Item Category': 'Previous Due Charges', 'Item Description': 'Handsets', 'Charges': previous_total_due, 'Data': 'NA', 'Minutes': 'NA', 'Messages': 'NA', 'Bill Cycle Date': 'NA', 'Invoice Number': 'NA', 'Note': 'NA'})
    if 'payment' in locals():
        result.append({'Account Number': 'NA', 'Wireless Number': 'NA', 'User Name': 'NA', 'Connection Type': 'NA', 'Address': 'NA', 'Item Category': 'Payment', 'Item Description': 'Handsets', 'Charges': payment, 'Data': 'NA', 'Minutes': 'NA', 'Messages': 'NA', 'Bill Cycle Date': 'NA', 'Invoice Number': 'NA', 'Note': 'NA'})
    for i, line in enumerate(lines):
        match = re.search(r'WHAT YOU NEED TO KNOW', line)
        if match:
            break
        if line.startswith('CHARGED USAGE'):
            break
        match = re.search(r'(.*?) (\d{9}) (\d{9}-\d{2})', line)
        if match:
            date = match.group(1)
            account = match.group(2)
            invoice = match.group(3)
        else:
            match = re.search(r'([A-Za-z]+\s+\d{2},\s+\d{4})\s+(\d{9})\s+(\d{9}-\d{1,2})', line)
            if match:
                date = match.group(1)
                account = match.group(2)
                invoice = match.group(3)
        match = re.search(r"\((\d{3})\) (\d{3}-\d{4}) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+)", line)
        if match:
            number = match.group(1)+' '+match.group(2)
            company = lines[i+1].split(' | ')[0]
            connection = lines[i+1].split(' | ')[1]
            address = lines[i+2]
            current_section = None
        match = re.search(r"(Account charges) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+)", line)
        if match:
            number = match.group(1)
            company = 'NA'
            connection = 'NA'
            address = 'NA'
            current_section = None

        if line.startswith('Connected device'):
            current_section = 'Regular Chagres'
        elif line.startswith('Voice line'):
            current_section = 'Regular Chagres'
        elif line.startswith('Charged Usage'):
            current_section = 'Usage Chagres'
        elif line.startswith('T-Mobile fees & charges'):
            current_section = 'Taxes & Fees'
        elif line.startswith('TAXES & FEES'):
            current_section = None
        elif line.startswith('Handsets'):
            current_section = 'Equipment'
            check = 1
        elif line.startswith('USAGE'):
            current_section = 'Usage'

        match = re.search(r"(.+?) (\$\d+\.\d+|\$\.\d+)", line)
        if current_section == 'Equipment':
            if check == 1:
                check = 0
            match = re.search('(\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+) (.+?)', lines[i+2])
            if match:
                result.append({'Account Number': account, 'Wireless Number': number, 'User Name': company, 'Connection Type': connection, 'Address': address, 'Item Category': current_section, 'Item Description': 'Handsets', 'Charges': match.group(1), 'Data': 'NA', 'Minutes': 'NA', 'Messages': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice, 'Note': lines[i+1]+' '+lines[i+2]+' '+lines[i+3]})
        elif match and current_section:
            if re.search(r"(.+ \$\d+\.\d+ .+|.+ \$\.\d+ .+)", line) or re.search(r"(USAGE CHARGES \$\d+\.\d+|USAGE CHARGES \-\$\d+\.\d+)", line):
                continue
            else:
                if number == 'Account charges':
                    result.append({'Account Number': account, 'Wireless Number': number, 'User Name': company, 'Connection Type': connection, 'Address': address, 'Item Category': current_section, 'Item Description': match.group(1), 'Charges': match.group(2), 'Data': 'NA', 'Minutes': 'NA', 'Messages': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice, 'Note': 'Included all Voice line Bus Unl Phone'})
                else:
                    result.append({'Account Number': account if 'account' in locals() else 'NA' , 'Wireless Number': number, 'User Name': company, 'Connection Type': connection, 'Address': address, 'Item Category': current_section, 'Item Description': match.group(1), 'Charges': match.group(2), 'Data': 'NA', 'Minutes': 'NA', 'Messages': 'NA', 'Bill Cycle Date': date if 'date' in locals() else 'NA', 'Invoice Number': invoice if 'invoice' in locals() else 'NA', 'Note': 'NA'})
        match = re.search(r'Data (\d+\.\d+ GB|\.\d+\ GB|\d+)', line)
        if match and current_section == 'Usage':
            result.append({'Account Number': account, 'Wireless Number': number, 'User Name': company, 'Connection Type': connection, 'Address': address, 'Item Category': current_section, 'Item Description': 'NA', 'Charges': 'NA', 'Data': match.group(1), 'Minutes': 'NA', 'Messages': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice, 'Note': 'NA'})
        match = re.search(r'Minutes (\d+\,\d+|\d+)', line)
        if match and current_section == 'Usage':
            result.append({'Account Number': account, 'Wireless Number': number, 'User Name': company, 'Connection Type': connection, 'Address': address, 'Item Category': current_section, 'Item Description': 'NA', 'Charges': 'NA', 'Data': 'NA', 'Minutes': match.group(1), 'Messages': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice, 'Note': 'NA'})
        match = re.search(r'Messages (\d+\,\d+|\d+)', line)
        if match and current_section == 'Usage':
            result.append({'Account Number': account, 'Wireless Number': number, 'User Name': company, 'Connection Type': connection, 'Address': address, 'Item Category': current_section, 'Item Description': 'NA', 'Charges': 'NA', 'Data': 'NA', 'Minutes': 'NA', 'Messages': match.group(1), 'Bill Cycle Date': date, 'Invoice Number': invoice, 'Note': 'NA'})
        match = re.search(r'Device discounts (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+)', line)
        if match and current_section == 'Usage':
            result.append({'Account Number': account, 'Wireless Number': number, 'User Name': company, 'Connection Type': connection, 'Address': address, 'Item Category': 'Monthly Discounts', 'Item Description': 'Device Discounts', 'Charges': match.group(1), 'Data': 'NA', 'Minutes': 'NA', 'Messages': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice, 'Note': 'NA'})

    df1 = pd.DataFrame(result)
    df1.to_csv(f'{output_directory}/{excelname}_details.csv', index=False)
    df1['Charges'] = df1['Charges'].str.replace('$', '').str.replace('NA', '0').astype(float)
    temp_check = df1
    df1 = df1.drop_duplicates(subset='Wireless Number')
    df1 = df1.drop(df.index[0])
    df1['Wireless Number'] = df1['Wireless Number'].str.replace(' ', '').str.replace('-', '')
    new_merged = pd.merge(df1,df,on='Wireless Number',how='inner')
    new_merged = new_merged[['Account Number', 'Wireless Number', 'User Name_x', 'Connection Type',
       'Address', 'Item Category', 'Item Description', 'Charges', 'Data',
       'Minutes', 'Messages', 'Bill Cycle Date', 'Invoice Number', 'Note',
       'Plan', 'User Name_y', 'Usage charges', 'Equipment',
       'Services', 'One-time charges', 'Taxes & Fees', 'Total']]
    
    pdf_df = new_merged[['Account Number','Wireless Number','Item Category','Item Description','Charges','Plan','User Name_x','Data','Total']]
    base_data_df = new_merged[['Account Number','Address','Invoice Number','Bill Cycle Date']]
    base_data_df = base_data_df.head(1)
    pdf_df = pdf_df.copy()
    
    rename_dict = {
        'User Name_x': 'User Name',
        'Plan': 'Plans',
        'Data': 'Data Usage',
        'Total': 'Total Charges',
        'Account Number': 'Account Number',
        'Wireless Number': 'Wireless Number',
        'Item Category': 'Item Category',
        'Item Description': 'Item Description'
    }
    pdf_df.columns = pdf_df.columns.map(lambda x: rename_dict.get(x, x))  # Rename if key exists

    rename_dict = {
        'User Name_x':'User Name',
        'Address':"Billing_Address",
        "Bill Cycle Date":"Duration"
    }
    base_data_df.columns = base_data_df.columns.map(lambda x: rename_dict.get(x, x)) 
    base_data_df.columns = base_data_df.columns.str.replace(' ', '_').str.lower()
    pdf_df.columns = pdf_df.columns.str.replace(' ', '_').str.lower()
    rename_dict = {
        'account_number': 'accountnumber',
        'invoice_number':'invoicenumber'
    }
    base_data_df.columns = base_data_df.columns.map(lambda x: rename_dict.get(x, x)) 
    print(base_data_df)
    unique_df['Total'] = (
        unique_df['Total']
        .replace(r'[^\d.-]', '', regex=True)  
        .astype(float)  
    )


    zippath = zip_folder(output_directory)
    shutil.rmtree(output_directory)
    print(zippath)
    return unique_df,base_data_df,temp_check

# path = "Bills/Analysis/Scripts/T-Mobile_Bill.pdf"
# try:
#     obj = extract_text_from_t_mobile_2(path)
# except Exception as e:
#     print(f"Error occurred while extracting text from T-Mobile bill: {str(e)}")