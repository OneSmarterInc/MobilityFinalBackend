print("verizon")

import re
import pandas as pd
import pdfplumber
from rest_framework.response import Response
from django.core.files.uploadedfile import UploadedFile
from io import BytesIO
from pathlib import Path
import os
from PyPDF2 import PdfReader
import PyPDF2


class PDFExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.result_df = None
        self.accounts_data = None
        self.bill_date_data = None
        self.net_amount = None
        self.key = None
        self.billing_address = {}

    def extract_data(self):
        Total_Charges_list = []
        duration = []
        bill_date = []
        dates, accounts, invoices, w = [], [], [], []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_number in range(2):  
                page = pdf.pages[page_number]
                text = page.extract_text()
                lines = text.split('\n')
                match = re.search(r"https?://.*", text)
                if match:
                    url = match.group()
                    w.append(url)
                
                for index, line in enumerate(lines):
                    if line.startswith('InvoiceNumber AccountNumber DateDue'):
                        line = lines[index + 1]
                        items = line.split()
                        del items[3]
                        del items[4]
                        del items[3]
                        date = items[2]
                        account = items[1]
                        invoice = items[0]
                        dates.append(date)
                        accounts.append(account)
                        invoices.append(invoice)
                    if "keyline" in line.lower():
                        self.key = "keyline"
                    if "total" in line.lower():
                        self.key = "total"
                    if self.key == "keyline":
                        match = re.match(r'^([A-Z\s]+,\s[A-Z]{2}\s\d{5}-\d{4})', line)
                        if match:
                            p2 = match.group(1)
                            p1 = re.sub(r'\bPayment\b.*', '', lines[index - 1])
                            print(f'{p1}{p2}')
                            self.billing_address["address"] = f'{p1}{p2}'

                match = re.search(r'Total Current Charges \$([\d,]+(?:\.\d{2})?)', text)
                if match:
                    total_charges = match.group(1)
                    Total_Charges_list.append(total_charges)
                else:
                    pattern = r'Total Current Charges Due by (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4} \$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
                    match = re.search(pattern, text)
                    if match:
                        total_charges = match.group(1)
                        Total_Charges_list.append(total_charges)                
                name_regex = re.compile(r'(?:\b[A-Z][A-Z\s.-]+\b)')

                names = name_regex.findall(text)
                global name_s
                name_s = names[-1] if names else None

                address_regex = re.compile(r'\b\d+\s[A-Z0-9\s.,-]+\b\s+[A-Z]{2}\s\d{5}-\d{4}')
                addresses = address_regex.findall(text)
                global address
                address = addresses[-1] if addresses else None


                match = re.search(r'Quick Bill Summary (\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s*-\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b)', text)
                if match:
                    phone_number = match.group(1)
                    duration.append(phone_number)

                match = re.search(r'Bill Date (January|February|March|April|May|June|July|August|September|October|November|December) (\d{2}), (\d{4})', text)
                if match:
                    phone_number = match.group(1)
                    amount = match.group(2)
                    pay = match.group(3)
                    bill_date.append({
                        "phone_number": phone_number,
                        "amount": amount,
                        "pay": pay
                    })

        bill_date1 = [f"{info['phone_number']} {info['amount']} {info['pay']}" for info in bill_date]

        df = pd.DataFrame({
            'Date_Due': dates,
            'AccountNumber': accounts,
            'InvoiceNumber': invoices,
            'Website': w,
            "Total_Current_Charges": Total_Charges_list,
            "Duration": duration,
            "Bill_Date": bill_date1
        })
        self.result_df = df
        self.accounts_data = accounts
        self.bill_date_data = bill_date1


    def extract_specific_lines_from_pdf(self, page_number, lines_to_extract):
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                page = pdf.pages[page_number - 1]
                text_lines = page.extract_text().splitlines()
                for line in text_lines:
                    match = re.search(r"Total\s*AmountDue\s*\$([\d,]+\.\d{2})", line)
                    if match:
                        self.net_amount =  match.group(1)
                        break
                lines = [line for i, line in enumerate(text_lines) if i + 1 in lines_to_extract]
                return lines
        except Exception as e:
            print(f"Error: {e}")
            return []

    def process_pdf(self, lines_to_extract):
        clnd_add = []
        extracted_lines = self.extract_specific_lines_from_pdf(1, lines_to_extract)
        
        for line_number, line_text in zip(lines_to_extract, extracted_lines):
            clnd_add.append(f"{line_text}")

        clnd_add = ' '.join(clnd_add)

        self.result_df["Client_Address"] = clnd_add
        self.result_df["Remidence_Address"] = "PO BOX 16810  NEWARK,NJ 07101-6522" * len(self.result_df)
        self.result_df['Billing_Name'] = name_s
        self.result_df['Billing_Address'] = address if address else 'Not_Available'


    def get_result_df(self):
        return self.result_df

    def get_accounts_info(self):
        return self.accounts_data
    
    def get_bill_date(self):
        return self.bill_date_data
    
    def get_net_amount(self):
        return self.net_amount
    def get_billing_address(self):
        return self.billing_address



class First:
    def __init__(self, path):
        self.path = path
        self.Lines = []
        self.line_re = re.compile(r'\d{3}-\d{3}-\d{4}')
        self.pdf = None
        self.wn_pattern = r'\d{3}[-.]\d{3}[-.]\d{4}'

    def parse_pdf(self):
        self.pdf = pdfplumber.open(self.path)
        pages = self.pdf.pages
        for page in self.pdf.pages:
            text = page.extract_text()
            self.parse_text(text)
        return self.Lines
    def parse_text(self, text):
        for line in text.split('\n'):

            if line.startswith('Account Charges (pg.2)'):
                items = line.split()
                items[1] = items[0]+' '+items[1]
                items[0] = '--'
                del items[2]
                del items[2]
                for i in range(3):
                    items.append('--')
                self.process_items(items)
            if self.line_re.search(line):
                items = line.split()
                items = items[:-3]

                if len(items) >= 12:
                    target_index = self.find_target_index(items)

                    if target_index is not None and target_index < len(items):
                        del items[target_index - 1]
                        items[1] = ' '.join(items[1:target_index - 1])
                        del items[2:target_index - 1]
                        self.process_items(items)

    def find_target_index(self, items):
        for i, element in enumerate(items):
            if i > 0 and (element.startswith('$') or (element.startswith('-') and '.' in element[1:])):
                return i
        return None

    def process_items(self, items):
        wn = items[0]
        if re.match(self.wn_pattern, wn):
            self.Lines.append({
                'Wireless_number': 'NA' if items[0] == '--' else items[0],
                'User_name': 'NA' if items[1] == '--' else items[1],
                'Monthly_Charges': 'NA' if items[2] == '--' else items[2],
                'Usage_and_Purchase_Charges': 'NA' if items[3] == '--' else items[3],
                'Equipment_Charges': 'NA' if items[4] == '--' else items[4],
                'Surcharges_and_Other_Charges_and_Credits': 'NA' if items[5] == '--' else items[5],
                'Taxes_Governmental_Surcharges_and_Fees': 'NA' if items[6] == '--' else items[6],
                'Third_Party_Charges_includes_Tax': 'NA' if items[7] == '--' else items[7],
                'Total_Charges': 'NA' if items[8] == '--' else items[8],
                'Voice_Plan_Usage': 'NA' if items[9] == '--' else items[9],
                'Messaging_Usage': 'NA' if items[10] == '--' else items[10],
                'Data_Usage': 'NA' if items[11] == '--' else items[11]
            })

def save_upload_file_tmp(upload_file: UploadedFile) -> str:
    temp_filename = os.path.join("/tmp", upload_file.name) 
    with open(temp_filename, "wb") as temp_file:
        for chunk in upload_file.chunks():
            temp_file.write(chunk)
    return temp_filename

class Model1():
    def __init__(self, q,accounts):
        self.pdf_data = q
        self.accounts = accounts
        self.data_new = None
        self.list1 = []
        self.lines = []

    def dim1(self, page, top_height):
        return 0, 0, page.width, top_height

    def dim2(self, page, top_height):
        return 0, top_height, page.width * 0.35, page.height

    def dim3(self, page, top_height):
        return page.width * 0.35, top_height, page.width, page.height

    def extraction(self, page, part_dims):
        if part_dims is None:
            return None
        return page.crop(part_dims).extract_text()

class Model2(Model1):
    def __init__(self, q,accounts):
        super().__init__(q,accounts)

    def max1(self):
        info = []
        with pdfplumber.open(self.pdf_data) as pdf:
            pages = len(pdf.pages)

        for num_page in range(pages):
            with pdfplumber.open(self.pdf_data) as pdf:
                page = pdf.pages[num_page]
                page_text = page.extract_text()
                if "Monthly_Charges" in page_text:
                    Lines = page_text.split("\n")
                    for line in Lines:
                        info.append(line)
        return info

    def max2(self, page):
        margin_left = page.bbox[0] + 510
        margin_top = page.bbox[1]
        margin_right = page.bbox[2]
        margin_bottom = page.bbox[3]
        page = page.crop((margin_left, margin_top, margin_right, margin_bottom))
        text = page.extract_text()
        Lines = text.split("\n")
        for line in Lines:
            match = re.search(
                r'(?:.*?(\$?\d+(?:\.\d+)?)|--)$',
                line)
            if match:
                self.list1.append(line)

    def max3(self):
        summary_pattern = re.compile(r'Summary for (.+?): (\d{3}-\d{3}-\d{4})')
        detail_pattern = re.compile(r'Detail for (.+?): (\d{3}-\d{3}-\d{4})')
        info1 = ''
        reader = PyPDF2.PdfReader(self.pdf_data)
        no_of_pages = len(reader.pages)
        # with pdfplumber.open(self.pdf_data) as pdf:
        #     for num_page in range(no_of_pages):
        #         page = pdf.pages[num_page]
        #         self.max2(page)
        #         print("max2 done!")
        #         page_text = page.extract_text()
        #         summary_match = summary_pattern.search(page_text)
        #         detail_match = detail_pattern.search(page_text)
        #         if summary_match or detail_match:
        #             if summary_match:
        #                 top_height = 0.15 * float(page.height)
        #                 top_part_text = self.extraction(page, self.dim1(page, top_height))
        #                 left_part_text = self.extraction(page, self.dim2(page, top_height))
        #                 right_part_text = self.extraction(page, self.dim3(page, top_height))
        #                 info1 = info1 + '\n' + top_part_text
        #                 info1 = info1 + '\n' + left_part_text
        #                 info1 = info1 + '\n' + right_part_text
        #             else:
        #                 detail_line_text = [line for line in page_text.split('\n') if detail_pattern.search(line)][0]
        #                 top_line = page_text.split('\n').index(detail_line_text)
        #                 top_height = top_line * float(page.height) / len(page_text.split('\n'))
        #                 top_part_text = self.extraction(page, (0, 0, page.width, top_height))
        #                 info1 += '\n' + top_part_text
        #         else:
        #             info1 = info1 + page_text + '\n'
        # self.info1 = info1
        # return info1
        for num_page in range(no_of_pages):
            with pdfplumber.open(self.pdf_data) as pdf:
                page = pdf.pages[num_page]
                self.max2(page)
                page_text = page.extract_text()
                summary_match = summary_pattern.search(page_text)
                detail_match = detail_pattern.search(page_text)
                if summary_match or detail_match:
                    if summary_match:
                        top_height = 0.15 * float(page.height)
                        top_part_text = self.extraction(page, self.dim1(page, top_height))
                        left_part_text = self.extraction(page, self.dim2(page, top_height))
                        right_part_text = self.extraction(page, self.dim3(page, top_height))
                        info1 = info1 + '\n' + top_part_text
                        info1 = info1 + '\n' + left_part_text
                        info1 = info1 + '\n' + right_part_text
                    else:
                        detail_line_text = [line for line in page_text.split('\n') if detail_pattern.search(line)][0]
                        top_line = page_text.split('\n').index(detail_line_text)
                        top_height = top_line * float(page.height) / len(page_text.split('\n'))
                        top_part_text = self.extraction(page, (0, 0, page.width, top_height))
                        info1 += '\n' + top_part_text
                else:
                    info1 = info1 + page_text + '\n'
            
        self.info1 = info1
        return info1

class Model3(Model2):
    def __init__(self, q,accounts):
        super().__init__(q,accounts)

    def data2(self):
        result = []
        current_section = None
        current_sections = None
        data = self.max3()
        lines = data.split('\n')
        check = 0
        start = 0
        list_not = ['Usage_and_Purchase_Charges', 'Voice', 'Messaging', 'Data', 'International']
        date = ""
        account = self.accounts[0]
        name = ""
        number = ""
        status = ""
        reg_list = []
        admo_list = []
        eco_list = []
        current_number_list = []
        center = ""
        plan = ""
        invoice = ""
        datam = " ".join(lines)
        check_dict = {}
        fake_dict = {}
        sake_dict = {}
        temp_list = []
        # Initialize dictionary to hold the charges
        charges_dict = {}

        # Extract relevant information
        current_number = None
        for line in lines:
            
            # Find the wireless number
            match = re.search(r'(?<!\d-)\b\d{3}-\d{3}-\d{4}\b', line)
            if match:
                current_number = match.group(0)
                charges_dict[current_number] = {'Name': '', 'Monthly Charge': '', 
                                                'Per Minute Charge': '', 'Account Share Charge': '', 
                                                'Monthly Gigabyte Allowance': '', 
                                                'Over Allowance Charge': '', 'Discount': '', 
                                                'Total Current Charge': '', 'Surcharges': {}, 
                                                'Other Charges and Credits': {}}

            # Extract details for the current number
            if current_number:
                if "Summary for" in line:
                    charges_dict[current_number]['Name'] = line.split(": ")[1]
                elif "monthlycharge" in line:
                    charges_dict[current_number]['Monthly Charge'] = line.split("$")[1].strip()
                elif "per minute" in line:
                    charges_dict[current_number]['Per Minute Charge'] = line.split("$")[1].strip()
                elif "Acct Share" in line:
                    charges_dict[current_number]['Account Share Charge'] = line.split("$")[1].strip()
                elif "gigabyte allowance" in line:
                    charges_dict[current_number]['Monthly Gigabyte Allowance'] = line.strip()
                elif "per GBafter allowance" in line:
                    charges_dict[current_number]['Over Allowance Charge'] = line.split("$")[1].strip()
                elif "Access Discount" in line:
                    charges_dict[current_number]['Discount'] = line.split("$")[0].strip()
                elif "Total Current Charges" in line:
                    charges_dict[current_number]['Total Current Charge'] = line.split("$")[1].strip()

            # Extract surcharges and other charges
            if current_number:
                if "Flex Business Data Device 2GB" in line and '-' in line:
                    check_dict = {'Wirelesss number':current_number,
                    'Charge':line[-6:]}
                    temp_list.append(check_dict)  
                elif "10% Access Discount" in line and '-' in line:
                    check_dict = {'Wirelesss number':current_number,
                    'Charge':line[-6:]}
                    temp_list.append(check_dict)
                elif "4G Mobile Broadband 5GB" in line and '-' in line:
                    check_dict = {'Wirelesss number':current_number,
                    'Charge':line[-6:]}
                    temp_list.append(check_dict)
                elif "Addl Smartphn Data Access" in line and '-' in line:
                    check_dict = {'Wirelesss number':current_number,
                    'Charge':line[-6:]}
                    temp_list.append(check_dict)
                elif "Business Unlimited Smartphon" in line and '-' in line:
                    check_dict = {'Wirelesss number':current_number,
                    'Charge':line[-6:]}
                    temp_list.append(check_dict)
                elif "Flexible Business Smartphn 2GB" in line and '-' in line:
                    check_dict = {'Wirelesss number':current_number,
                    'Charge':line[-6:]}
                    temp_list.append(check_dict)
                elif "Flexible Business S martphn 2GB" in line and '-' in line:
                    check_dict = {'Wirelesss number':current_number,
                    'Charge':line[-6:]}
                    temp_list.append(check_dict)                                     
                elif "Regulatory Charge" in line:
                    check_dict = {'Wirelesss number':current_number,
                    'Charge':line[-4:]}
                    temp_list.append(check_dict)
                    reg_list.append(line[-4:])
                    charges_dict[current_number]['Surcharges']['Regulatory Charge'] = line[-4:]
                elif "Administrative Charge" in line:
                    fake_dict = { 'Wirelesss number':current_number,
                    'Charge':line[-4:]}
                    temp_list.append(fake_dict)
                    admo_list.append(line[-4:])
                    charges_dict[current_number]['Surcharges']['Administrative Charge'] = line[-4:]
                elif "Economic Adjustment Charge" in line:
                    sake_dict = {'Wirelesss number':current_number,
                    'Charge':line[-4:]}
                    temp_list.append(sake_dict)
                    eco_list.append(line[-4:])
                    charges_dict[current_number]['Other Charges and Credits']['Economic Adjustment Charge'] = line[-4:]
                elif 'OH Tax Recovery Surcharge' in line:
                    sake_dict = {'Wirelesss number':current_number,
                    'Charge':line[-4:]}
                    temp_list.append(sake_dict)
                elif 'Fed Universal Service Charge' in line:
                    sake_dict = {'Wirelesss number':current_number,
                    'Charge':line[-4:]}
                    temp_list.append(sake_dict)
                elif 'WA State 911 Fee' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict)
                elif 'WA State 988 Tax' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict)
                elif 'Kitsap Cnty 911 Surchg' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict)
                elif 'WA State Sales Tax-Telecom' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict)
                elif 'Kitsap Cnty Sales Tax-Telecom' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict)
                elif 'MO State Sls Tax-Telco' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict)
                elif 'Overland Loc BUS Lic Surchg' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict)
                elif 'Saint Louis Cnty Sls Tax-Telco' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict)
                elif 'Overland Cty Sls Tax-Telco' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict)
                elif 'Jefferson Cnty Sls Tax-Telco' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict) 
                elif 'Jefferson Cnty Dst Tax-Telco' in line:
                    sake_dict = {'Wireless number': current_number, 'Charge': line[-4:]}
                    temp_list.append(sake_dict)        
                                  
        # Output the charges dictionary
        # print('>>>>>>>>>>><<<<')
        # print(charges_dict)
        # lenght_of_eco = len(eco_list)
        # additional = lenght_of_eco-len(reg_list)
        # for i in range(additional):
        #     reg_list.append('NA')
        #     admo_list.append('NA')
        # charges_dict = {
        #     'Regulatory Charges':reg_list,
        #     'Adminstrative Charges':admo_list,
        #     'Economic Adjustment Charges':eco_list
        # }

        # df_charge = pd.DataFrame(charges_dict)
        # dir = 'output'
        # filename = 'final.csv'
        # path = os.path.join(d[-4:]
        # df_charge.to_csv(path,index=False)
        df_df = pd.DataFrame(temp_list)

        # Verify number of columns and rename accordingly
        if df_df.shape[1] == 2:
            df_df.columns = ['Wireless number', 'Charge']
        elif df_df.shape[1] == 3:
            df_df.columns = ['Wireless number', 'Charge', 'RCB']
        else:
            raise ValueError(f"Unexpected number of columns: {df_df.shape[1]}")

        # Convert 'Charge' column to numeric if it exists
        if 'Charge' in df_df.columns:
            df_df['Charge'] = pd.to_numeric(df_df['Charge'].str.strip(), errors='coerce')

        # Rename columns
        df_df.rename(columns={'Wireless number': 'Wireless_number', 'Charge': 'Current_Charges'}, inplace=True)


        # dir = 'output'
        # filename = 'finalaa.csv'
        # path = os.path.join(dir,filename)
        # df.to_csv(path,index=False)
        # pattern = re.compile(r"Summary for (.*?): (\d{3}-\d{3}-\d{4}).*?Monthly Charges.*?(\$[\d.]+ monthlycharge).*?(\$[\d.]+ per minute).*?(\d+GB Acct Share \$\d+/GB).*?(\d+monthlygigabyte allowance).*?(\$[\d.]+per GBafter allowance).*?10% Access Discount.*?(\$[\d.-]+).*?Total Current Charges for \d{3}-\d{3}-\d{4} (\$[\d.]+)")
        # matches = pattern.findall(str_data)

        # # Create a dictionary to store the extracted information
        # charges_dict = {}

        # for match in matches:
        #     name = match[0].strip()
        #     number = match[1].strip()
        #     monthly_charge = match[2].strip()
        #     per_minute_charge = match[3].strip()
        #     acct_share_charge = match[4].strip()
        #     monthly_gb_allowance = match[5].strip()
        #     over_allowance_charge = match[6].strip()
        #     discount = match[7].strip()
        #     total_current_charge = match[8].strip()

        #     charges_dict[number] = {
        #         'Name': name,
        #         'Monthly Charge': monthly_charge,
        #         'Per Minute Charge': per_minute_charge,
        #         'Account Share Charge': acct_share_charge,
        #         'Monthly Gigabyte Allowance': monthly_gb_allowance,
        #         'Over Allowance Charge': over_allowance_charge,
        #         'Discount': discount,
        #         'Total Current Charge': total_current_charge
        #     }

        # # Print the extracted charges dictionary
        # print('>>>>>>>><<<<<')
        # print(charges_dict)

        def split_list(lst):

            words = ["Calling", "Mobile", "Night/Weekend", "Text", "Unlimited", "Picture", "Gigabyte"]
            indices = [i for i, word in enumerate(lst) if word in words]

            if indices and indices[0] != 0:
                return lst[indices[0]:]
            else:
                return lst
        for line in lines:
            if re.search(r"^[A-Z].*\d+.*-- --$", line):
                items = line.split()
                items = split_list(items)
                if items[0] == 'Unlimited' and items[1] == 'OFFPEAK':
                    items = items[2:]
                items1 = ' '.join(items[:-5])
                items4 = items[-5:]
                items = [items1] + items4
                if current_sections == 'Data':
                    try:
                        value = float(items[2])
                        if isinstance(value, float):
                            items[2] = items[2]+'(shared)'
                            temp = 2
                    except ValueError:
                        temp = 3
                    result.append({'Foundation Account': 'NA', 'Account Number': account, 'Group Number': 'NA', 'User Name': name, 'Wireless Number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': 'NA', 'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': current_sections, 'Item Type': items[1], 'Item Description': items[0], 'Share Description': 'Shared Usage' if temp == 2 else 'NA', 'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': items[2], 'Used': float(items[3]), 'Billable': float(0) if items[4] == '--' else items[4], 'Charges': float(0) if items[5] == '--' else float(items[5]), 'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                else:
                    result.append({'Foundation Account': 'NA', 'Account Number': account, 'Group Number': 'NA', 'User Name': name, 'Wireless Number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': 'NA', 'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': current_sections, 'Item Type': items[1], 'Item Description': items[0], 'Share Description': 'NA', 'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': items[2], 'Used': float(items[3]), 'Billable': float(0) if items[4] == '--' else items[4], 'Charges': float(0) if items[5] == '--' else float(items[5]), 'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                continue
            else:
                if current_sections == 'Data':
                    if re.search(r'Gigabyte Usage gigabytes', line):
                        items = line.split()
                        items = items[-7:]
                        try:
                            value = float(items[3])
                            if isinstance(value, float):
                                items[3] = items[3]+'(shared)'
                                temp = 2
                        except ValueError:
                            temp = 3
                        result.append({'Foundation Account': 'NA', 'Account Number': account, 'Group Number': 'NA', 'User Name': name, 'Wireless Number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': 'NA', 'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': current_sections, 'Item Type': items[2], 'Item Description': items[0:2], 'Share Description': 'Shared Usage' if temp == 2 else 'NA', 'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': items[3], 'Used': float(items[4]), 'Billable': float(0) if items[5] == '--' else items[5], 'Charges': float(0) if items[6] == '--' else float(items[6]), 'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                        continue
                match = re.search(r"(\d{2}/\d{2}) - (\d{2}/\d{2}) Travelpass - (.+) \(\$([\d.]+) Per Day\) \$([\d.]+)", line)
            if match:

                    destination = match.group(1)+' '+match.group(2)+' '+match.group(3)+' '+match.group(4)
                    total_cost = float(match.group(5))

                    result.append({
                        'Foundation Account': 'NA',
                        'Account Number': account,
                        'Group Number': 'NA',
                        'User Name': name,
                        'Wireless Number': number,
                        'User Email': 'NA',
                        'Status': status,
                        'Cost Center': 'NA',
                        'Account Charges and Credits': 'NA',
                        'Plans': plan,
                        'Item Category': current_section,
                        'Item Type': 'NA',
                        'Item Description': f"Travelpass - {destination}",
                        'Share Description': 'NA',
                        'Share Voice': 'NA',
                        'Share Messaging': 'NA',
                        'Share Data': 'NA',
                        'Allowance': 'NA',
                        'Used': 'NA',
                        'Billable': 'NA',
                        'Charges': total_cost,
                        'Order Details': 'NA',
                        'Bill Cycle Date': date,
                        'Invoice Number': invoice})
                    continue

            if line.startswith(r"International Minutes") or line.startswith(r"International Message"):
                    items = line.split()
                    result.append({
                        'Foundation Account': 'NA',
                        'Account Number': account,
                        'Group Number': 'NA',
                        'User Name': name,
                        'Wireless Number': number,
                        'User Email': 'NA',
                        'Status': status,
                        'Cost Center': 'NA',
                        'Account Charges and Credits': 'NA',
                        'Plans': plan,
                        'Item Category': current_section,
                        'Item Type': 'NA',
                        'Item Description': str(items[0]+' '+items[1]),
                        'Share Description': 'NA',
                        'Share Voice': 'NA',
                        'Share Messaging': 'NA',
                        'Share Data': 'NA',
                        'Allowance': 'NA',
                        'Used': 'NA',
                        'Billable': 'NA',
                        'Charges': float(items[-1].replace('$','')),
                        'Order Details': 'NA',
                        'Bill Cycle Date': date,
                        'Invoice Number': invoice})
                    continue

            match = re.search(r'^([^0-9]+)\s+([-+]?\d*\.\d+|\d+)$', line)
            if match and current_section:
                result.append({
                    'Foundation Account': 'NA',
                    'Account Number': account,
                    'Group Number': 'NA',
                    'User Name': name,
                    'Wireless Number': number,
                    'User Email': 'NA',
                    'Status': status,
                    'Cost Center': 'NA',
                    'Account Charges and Credits': 'NA',
                    'Plans': plan,
                    'Item Category': current_section,
                    'Item Type': 'NA',
                    'Item Description': match.group(1).strip(),
                    'Share Description': 'NA',
                    'Share Voice': 'NA',
                    'Share Messaging': 'NA',
                    'Share Data': 'NA',
                    'Allowance': 'NA',
                    'Used': 'NA',
                    'Billable': 'NA',
                    'Charges': float(match.group(2)),
                    'Order Details': 'NA',
                    'Bill Cycle Date': date,
                    'Invoice Number': invoice
                })
                continue

            match = re.search(r'^([^0-9]+ \d+ [^0-9]+) (\d*\.\d+)$', line)
            if match and current_section:
                result.append({
                    'Foundation Account': 'NA',
                    'Account Number': account,
                    'Group Number': 'NA',
                    'User Name': name,
                    'Wireless Number': number,
                    'User Email': 'NA',
                    'Status': status,
                    'Cost Center': 'NA',
                    'Account Charges and Credits': 'NA',
                    'Plans': plan,
                    'Item Category': current_section,
                    'Item Type': 'NA',
                    'Item Description': match.group(1).strip(),
                    'Share Description': 'NA',
                    'Share Voice': 'NA',
                    'Share Messaging': 'NA',
                    'Share Data': 'NA',
                    'Allowance': 'NA',
                    'Used': 'NA',
                    'Billable': 'NA',
                    'Charges': float(match.group(2)),
                    'Order Details': 'NA',
                    'Bill Cycle Date': date,
                    'Invoice Number': invoice
                })
                continue

            match = re.search(r"(?P<name>.+?)\s+(?P<value>[+-]?\d+\.\d{2})", line)
            if match and current_section:
                if match.group(1).strip() == 'Gigabyte Usage gigabytes' or match.group(1).strip() == 'Gigabyte Usage gigabytes unlimited':
                    pass
            else:
                result.append({
                        'Foundation Account': 'NA',
                        'Account Number': account,
                        'Group Number': 'NA',
                        'User Name': name,
                        'Wireless Number': number,
                        'User Email': 'NA',
                        'Status': status,
                        'Cost Center': 'NA',
                        'Account Charges and Credits': 'NA',
                        'Plans': plan,
                        'Item Category': current_section,
                        'Item Type': 'NA',
                        'Item Description': 'NA',
                        'Share Description': 'NA',
                        'Share Voice': 'NA',
                        'Share Messaging': 'NA',
                        'Share Data': 'NA',
                        'Allowance': 'NA',
                        'Used': 'NA',
                        'Billable': 'NA',
                        'Charges': float(match.group(2)) if match else 'NA',
                        'Order Details': 'NA',
                        'Bill Cycle Date': date,
                        'Invoice Number': invoice
                    })
                continue

            match = re.search(r"b2b.verizonwireless.com.\s*(.*?)\s*([\d.]+)", line)
            if match and current_section == 'Surcharges':
                result.append({
                        'Foundation Account': 'NA',
                        'Account Number': account,
                        'Group Number': 'NA',
                        'User Name': name,
                        'Wireless Number': number,
                        'User Email': 'NA',
                        'Status': status,
                        'Cost Center': 'NA',
                        'Account Charges and Credits': 'NA',
                        'Plans': plan,
                        'Item Category': current_section,
                        'Item Type': 'NA',
                        'Item Description': match.group(1).strip(),
                        'Share Description': 'NA',
                        'Share Voice': 'NA',
                        'Share Messaging': 'NA',
                        'Share Data': 'NA',
                        'Allowance': 'NA',
                        'Used': 'NA',
                        'Billable': 'NA',
                        'Charges': float(match.group(2)),
                        'Order Details': 'NA',
                        'Bill Cycle Date': date,
                        'Invoice Number': invoice
                    })
                continue

            match = re.search(r"(.+?)\s+\$([\d.]+)", line)
            if match and current_section == 'Usage and Purchase Charges':
                result.append({
                        'Foundation Account': 'NA',
                        'Account Number': account,
                        'Group Number': 'NA',
                        'User Name': name,
                        'Wireless Number': number,
                        'User Email': 'NA',
                        'Status': status,
                        'Cost Center': 'NA',
                        'Account Charges and Credits': 'NA',
                        'Plans': plan,
                        'Item Category': current_section,
                        'Item Type': 'NA',
                        'Item Description': match.group(1).strip(),
                        'Share Description': 'NA',
                        'Share Voice': 'NA',
                        'Share Messaging': 'NA',
                        'Share Data': 'NA',
                        'Allowance': 'NA',
                        'Used': 'NA',
                        'Billable': 'NA',
                        'Charges': float(match.group(2)),
                        'Order Details': 'NA',
                        'Bill Cycle Date': date,
                        'Invoice Number': invoice
                    })
                continue
        # At this point, 'result' will contain the desired data structure
        result   
        chrage_result = result
        charges_df = pd.DataFrame(chrage_result)
        require_df = charges_df[['Charges']]
        result = []     


        for i, line in enumerate(lines):
            match1 = re.search(r'Bill Date (.+? \d{4})', line)
            match2 = re.search(r'Account number (\d{9}-\d{5})', line)
            match3 = re.search(r'Invoice Number (\d{10})', line)
            if match1:
                date = match1.group(1)
            if match2:
                account = match2.group(1)
            if match3:
                invoice = match3.group(1)
            if line.startswith('Account Charges (pg.2)'):
                items = line.split()
                items[1] = items[0] + ' ' + items[1]
                items[0] = '--'
                del items[2]
                result.append({
                    'Foundation Account': 'NA',
                    'Account_number': account,
                    'Group Number': 'NA',
                    'User_name': 'NA' if items[1] == '--' else items[1],
                    'Wireless_number': 'NA',
                    'User Email': 'NA',
                    'Status': 'Inactive',
                    'Cost Center': 'NA',
                    'Account Charges and Credits': 'NA' if items[2] == '--' else items[2],
                    'Plans': 'NA',
                    'Item Category': 'NA',
                    'Item Type': 'NA',
                    'Item Description': 'NA',
                    'Share Description': 'NA',
                    'Share Voice': 'NA',
                    'Share Messaging': 'NA',
                    'Share Data': 'NA',
                    'Allowance': 'NA',
                    'Used': 'NA',
                    'Billable': 'NA',
                    'Charges': ' NA' if items[9] == '--' else items[9],
                    'Order Details': 'NA',
                    'Bill Cycle Date': date,
                    'Invoice Number': invoice
                })

                break
            elif line.startswith('Account Plan and Charges** (pg.2)'):
                items = line.split()
                items[1] = items[0] + ' ' + items[1] + ' ' + items[2] + ' ' + items[3]
                items[0] = '--'
                for i in range(3):
                    del items[2]
                result.append({
                    'Foundation Account': 'NA',
                    'Account_number': account,
                    'Group Number': 'NA',
                    'User_name': 'NA' if items[1] == '--' else items[1],
                    'Wireless_number': 'NA',
                    'User Email': 'NA',
                    'Status': 'Inactive',
                    'Cost Center': 'NA',
                    'Account Charges and Credits': 'NA' if items[2] == '--' else items[2],
                    'Plans': 'NA',
                    'Item Category': 'NA',
                    'Item Type': 'NA',
                    'Item Description': 'NA',
                    'Share Description': 'NA',
                    'Share Voice': 'NA',
                    'Share Messaging': 'NA',
                    'Share Data': 'NA',
                    'Allowance': 'NA',
                    'Used': 'NA',
                    'Billable': 'NA',
                    'Charges': 'NA' if items[9] == '--' else items[9],
                    'Order Details': 'NA',
                    'Bill Cycle Date': date,
                    'Invoice Number': invoice
                })
                break
        for i, line in enumerate(lines):
            click_count = 0
            match = re.search(r'Summary for (.+?): (\d{3}-\d{3}-\d{4})', line)
            if match:
                start = 1
                name = match.group(1)
                number = match.group(2)
                center = lines[i + 1]
                if center == 'Your Plan':
                    center = 'NA'
                for item in self.lines:
                    if item.get('Wireless_number') == number and item.get('User_name') == name:
                        status = float(item.get('Monthly_Charges').replace('$', ''))
                        status = 'Active' if status > 0 else 'Inactive'
                        break
            if line.startswith('Your Plan'):
                match = re.search(r'(.*GB$|.*MB$)', lines[i + 1])
                if match:
                    plan = lines[i + 1]
                match = re.search(r'(.*GB$|.*MB$)', lines[i + 2])
                if match:
                    plan = lines[i + 2]
                else:
                    plan = lines[i + 1]
            if start != 0:
                if line.startswith('Monthly_Charges'):
                    current_section = 'Monthly_Charges'
                elif line.startswith('EquipmentCharges'):
                    current_section = 'Equipment_Charges'
                elif line.startswith('Usage_and_Purchase_Charges'):
                    current_section = 'Usage_and_Purchase_Charges'
                elif line.startswith('Surcharges') or line.startswith('Surcharges+'):
                    current_section = 'Surcharges'
                elif line.startswith('OtherChargesandCredits'):
                    current_section = 'Other Charges and Credits'
                elif line.startswith('Taxes_Governmental_Surcharges_and_Fees') or line.startswith(
                        'Taxes_Governmental_Surcharges_and_Fees+'):
                    current_section = 'Taxes_Governmental_Surcharges_and_Fees'
                elif line.startswith('Total Current Charges for'):
                    current_section = None

                match = re.search(
                    r'(.+? \d+\.\d+ .+?|.+?) (\.\d+|\d+\.\d+|\d+\,\d+\.\d+|\-\.\d+|\-\d+\.\d+|\-\d+\,\d+\.\d+)',
                    line)
                if 'Flexible Business S martphn 2GB'in line  and '-' in line:
                        result.append({'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                                'User_name': name,
                                'Wireless_number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                                'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': 'Monthly Charges',
                                'Item Type': 'NA', 'Item Description': 'Flexible Business Smartphn 2GB' , 'Share Description': 'NA',
                                'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                                'Used': 'NA', 'Billable': 'NA',
                                'Charges': 'NA',
                                'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                elif 'Flex Business Data Device 2GB' in line and '-' in line:
                    result.append({'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                             'User_name': name,
                             'Wireless_number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                             'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': 'Monthly Charges',
                             'Item Type': 'NA', 'Item Description': 'Flex Business Data Device 2GB' , 'Share Description': 'NA',
                             'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                             'Used': 'NA', 'Billable': 'NA',
                             'Charges': 'NA',
                             'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                elif '10% Access Discount' in line and '-' in line :
                    result.append({'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                             'User_name': name,
                             'Wireless_number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                             'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': 'Monthly Charges',
                             'Item Type': 'NA', 'Item Description': '10% Access Discount' , 'Share Description': 'NA',
                             'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                             'Used': 'NA', 'Billable': 'NA',
                             'Charges': 'NA',
                             'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                elif '4G Mobile Broadband 5GB' in line and '-' in line :
                    result.append({'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                             'User_name': name,
                             'Wireless_number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                             'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': 'Monthly Charges',
                             'Item Type': 'NA', 'Item Description': '4G Mobile Broadband 5GB' , 'Share Description': 'NA',
                             'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                             'Used': 'NA', 'Billable': 'NA',
                             'Charges': 'NA',
                             'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                elif 'Addl Smartphn Data Access' in line and '-' in line :
                    result.append({'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                             'User_name': name,
                             'Wireless_number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                             'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': 'Monthly Charges',
                             'Item Type': 'NA', 'Item Description': 'Addl Smartphn Data Access' , 'Share Description': 'NA',
                             'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                             'Used': 'NA', 'Billable': 'NA',
                             'Charges': 'NA',
                             'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                elif 'Business Unlimited Smartphone' in line and '-' in line :
                    result.append({'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                             'User_name': name,
                             'Wireless_number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                             'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': 'Monthly Charges',
                             'Item Type': 'NA', 'Item Description': 'Business Unlimited Smartphone' , 'Share Description': 'NA',
                             'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                             'Used': 'NA', 'Billable': 'NA',
                             'Charges': 'NA',
                             'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})   
                elif 'Flexible Business Smartphn 2GB' in line and '-' in line :
                    result.append({'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                             'User_name': name,
                             'Wireless_number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                             'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': 'Monthly Charges',
                             'Item Type': 'NA', 'Item Description': 'Flexible Business Smartphn 2GB' , 'Share Description': 'NA',
                             'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                             'Used': 'NA', 'Billable': 'NA',
                             'Charges': 'NA',
                             'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})                                                 

                if match and (current_section not in list_not and current_section != None) and (
                        match.group(2) in self.list1 and 'Due' not in line):
                    if check == 1:
                        check = 0
                        result.append(
                            {'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                             'User_name': name,
                             'Wireless_number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                             'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': current_section,
                             'Item Type': 'NA', 'Item Description': match.group(1), 'Share Description': 'NA',
                             'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                             'Used': 'NA', 'Billable': 'NA',
                             'Charges': 'NA' if match.group(2) == "--" or " " else match.group(2),
                             'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                    else:
                        result.append(
                            {'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                             'User_name': name,
                             'Wireless_number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                             'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': current_section,
                             'Item Type': 'NA', 'Item Description': match.group(1), 'Share Description': 'NA',
                             'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA',
                             'Allowance': 'NA',
                             'Used': 'NA', 'Billable': 'NA',
                             'Charges': 'NA' if match.group(2) == "--" or " " else match.group(2),
                             'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})

                if current_section == 'Usage_and_Purchase_Charges':
                    if re.search(r"Voice Allowance Used Billable Cost", line):
                        current_sections = 'Voice'
                    elif re.search(r"Messaging Allowance Used Billable Cost", line):
                        current_sections = 'Messaging'
                    elif re.search(r"Data Allowance Used Billable Cost", line):
                        current_sections = 'Data'
                    elif line.startswith('International Allowance Used Billable Cost'):
                        current_sections = 'International'
                    if "unlimited" not in line and ('Calling' in line) or (
                            'Gigabyte' in line and 'shared' not in lines[i + 1]) or (
                            "Shared" in line and "unlimited" not in line):
                        if "Shared" in line and "unlimited" not in line:
                            words = line.split()
                            words.insert(2, "NA")
                            line = ' '.join(words)
                        else:
                            words = line.split()
                            words.insert(3, "NA")
                            line = ' '.join(words)
                    match = re.search(
                        r'(.+?) (minutes|messages|gigabytes) (unlimited|\.\d+|\d+\.\d+|\d+\,\d+\.\d+|\-\.\d+|\-\d+\.\d+|\-\d+\,\d+\.\d+|\--) (.+) (.+) (.+)',
                        line)
                    match_I = re.search(
                        r'(International\s*Minutes)\s*(minutes|messages)\s*(\d+)\s*(\d+)\s*(-?\$\d{1,3}(?:,\d{3})*\.\d+)',
                        line)
                    if current_sections == "International" or match_I:
                        if match:
                            result.append({'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                                           'User_name': name, 'Wireless_number': number, 'User Email': 'NA',
                                           'Status': status, 'Cost Center': center, 'Account Charges and Credits': 'NA',
                                           'Plans': plan, 'Item Category': current_sections,
                                           'Item Type': match.group(2),
                                           'Item Description': match.group(1), 'Share Description': 'NA',
                                           'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA',
                                           'Allowance': match.group(3),
                                           'Used': match.group(4), 'Billable': match.group(5),
                                           'Charges': 'NA' if match.group(6) == "--" or " " else match.group(6),
                                           'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                        if match_I:
                            result.append(
                                {'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                                 'User_name': name, 'Wireless_number': number, 'User Email': 'NA', 'Status': status,
                                 'Cost Center': center, 'Account Charges and Credits': 'NA', 'Plans': plan,
                                 'Item Category': current_sections, 'Item Type': match_I.group(2),
                                 'Item Description': match_I.group(1), 'Share Description': 'NA',
                                 'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA',
                                 'Allowance': match_I.group(3),
                                 'Used': match_I.group(4), 'Billable': match_I.group(5),
                                 'Charges': 'NA' if match_I.group(5) == "--" or " " else match_I.group(5),
                                 'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                    else:
                        if match:
                            result.append({'Foundation Account': 'NA', 'Account_number': account, 'Group Number': 'NA',
                                           'User_name': name, 'Wireless_number': number, 'User Email': 'NA',
                                           'Status': status, 'Cost Center': center, 'Account Charges and Credits': 'NA',
                                           'Plans': plan, 'Item Category': current_sections,
                                           'Item Type': match.group(2),
                                           'Item Description': match.group(1), 'Share Description': 'NA',
                                           'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA',
                                           'Allowance': match.group(3),
                                           'Used': match.group(4), 'Billable': match.group(5),
                                           'Charges': 'NA' if match.group(6) == "--" or " " else match.group(6),
                                           'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
        self.result = result
        return result,require_df,df_df

class Model4(First, Model3):
    def __init__(self, q,accounts):
        super().__init__(q)
        self.pdf_data = q
        self.accounts = accounts
        self.list1 = []

    def process_pdf(self):
        lines = self.parse_pdf()
        
        self.lines = lines
        data_from_model3,rdf,df_df = self.data2()
        df_lines = pd.DataFrame(lines)
        df_model3 = pd.DataFrame(data_from_model3)
        df_model3['Charges'] = rdf['Charges']

        print(df_lines.columns)
        print(df_model3.columns)
        print(df_df)
        merged_df = pd.merge(df_lines, df_model3, left_on='Wireless_number', right_on='Wireless_number', how='left')
        merged_df['Charges'] = df_df['Current_Charges']
        
        print(merged_df[['Wireless_number','Item Category','Item Description','Charges']])
        duplicate_df = merged_df
        merged_df = merged_df.drop_duplicates(subset='Wireless_number')
        merged_df = merged_df.reset_index(drop=True)
        duplicate_df['ECPD Profile ID'] = 'NA'
        duplicate_df['User ID'] = 'NA'
        new_columns = ['Data Usage (KB)','Data Usage (MB)','Voice Roaming','Messaging Roaming','Data Roaming (KB)','Data Roaming (MB)','Data Roaming (GB)']
        for y in new_columns:
            duplicate_df[y] = 0 
        duplicate_df.rename(columns={'Plans':"Your Calling Plans",'Data_Usage':'Data Usage(GB)'},inplace=True)
        merged_df.rename(columns={'User_name_x':'user_name'},inplace=True)
        merged_df.drop(columns=['User_name_y', 'Item Type', 'Share Description', 'Share Voice',
       'Share Messaging', 'Share Data', 'Allowance', 'Used', 'Billable', 'Order Details','Bill Cycle Date', 'Invoice Number'],inplace=True)
        return merged_df,duplicate_df



def extract_total_data(result,tmp_df):
    temp_result_df = result
    df_unique = temp_result_df.drop_duplicates(subset=['Wireless_number'])
    df_unique_dict = df_unique.to_dict(orient='records')

    ### main
    total_dict = df_unique_dict
    result_df = result
    for entry in total_dict:
        entry['company'] = "Simpletek"
        entry['vendor'] = "Verizon"
        entry['sub_company'] = "BABW"
        entry['location'] = "Shegaon"
    res_data_dict = result_df.to_dict(orient='records')
    for entry in res_data_dict:
        entry['company'] = "Simpletek"
        entry['vendor'] = "Verizon"
        entry['sub_company'] = "BABW"
        entry['location'] = "Shegaon"
    return res_data_dict,total_dict,tmp_df
# path = 'Bills/media/BanUploadBill/mob_1175_34212553900001_06152024_9966671861.pdf'
# lines_to_extract = [2, 3, 4, 5]

# extractor = PDFExtractor(path)
# extractor.extract_data()
# extractor.process_pdf(lines_to_extract)
# acc_info = extractor.get_accounts_info()
# extractor = Model4(path,acc_info)
# result,tmp_df = extractor.process_pdf()
# pdf_data, unique_pdf_data,tmp_df = extract_total_data(result,tmp_df)
# print(tmp_df[['Wireless_number','Item Category','Item Description','Charges']])
