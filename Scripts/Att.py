print("ATT")

import re
import pdfplumber
import pandas as pd

class first_page_extractor:
    print("def first_page_extractor")
    def __init__(self,input_file):
        print("def __init__")
        self.input_path = input_file
        self.Lines_1 = None
        pages_data = []
        with pdfplumber.open(self.input_path) as pdf:
            num_of_pages = len(pdf.pages)
        if num_of_pages < 3500:
            with pdfplumber.open(self.input_path) as pdf:
                pages_data = [page.extract_text() for page in pdf.pages[:2]]
            for page_data in pages_data:
                first_page_data = page_data
                break

            self.first_page_data_dict= {
                "Bill_Date": None,
                "AccountNumber": None,
                "foundation_account": None,
                "InvoiceNumber": None,
                "Billing_Name":None,
                "Billing_Address":None,
                "Remidence_Address":None}
            
        for line in first_page_data.splitlines():
            if line.startswith("Issue Date:"):
                self.first_page_data_dict["Bill_Date"] = line.split(": ")[-1]
            elif line.startswith("Account Number:") or "Account Number" in line:
                self.first_page_data_dict["AccountNumber"] = line.split(": ")[-1]
            elif line.startswith("Foundation Account:"):
                self.first_page_data_dict["foundation_account"] = line.split(": ")[-1]
            elif line.startswith("Invoice:"):
                self.first_page_data_dict["InvoiceNumber"] = line.split(": ")[-1]

            self.first_page_data_dict['Billing_Name'] = re.search(r"^(.*?)\n", first_page_data).group(1)
            self.first_page_data_dict['Billing_Address'] = re.search(r"\n(.*?)\n", first_page_data).group(1)
            self.first_page_data_dict['Remidence_Address'] = "PO Box 6463 Carol Stream, IL 60197-646"

    def first_page_data_func(self):
        print("def first_page_data_func")
        return self.first_page_data_dict
    def get_acc_info(self):
        print("def get_acc_info")
        return self.first_page_data_dict['AccountNumber']
    def get_bill_date_info(self):
        return self.first_page_data_dict['Bill_Date']
    def get_invoice_number_info(self):
        return self.first_page_data_dict['InvoiceNumber']
    def get_foundation_account(self):
        return self.first_page_data_dict['foundation_account']

class Att:
    def __init__(self, input_file):
        self.input_path = input_file
        self.Lines_1 = None
        self.no_pages = None
        extracted_data = []
        pages_data = []
        with pdfplumber.open(self.input_path) as pdf:
            num_of_pages = len(pdf.pages)
            self.no_pages = num_of_pages
        if num_of_pages <= 100:
            with pdfplumber.open(self.input_path) as pdf:
                pages_data = [page.extract_text() for page in pdf.pages]
            temp_pages_data = '\n'.join(pages_data)  # Correctly join all page texts into a single string
            temp_lines = temp_pages_data.split('\n')
            data_pattern = re.compile(r"(\d{3}\.\d{3}\.\d{4})\s+([A-Z\s]+)\s+([\d\.]+)\s+(\d+)\s+(\d+)")
            for line in temp_lines:
                match = data_pattern.search(line)
                if match:
                    number = match.group(1)
                    user = match.group(2).strip()
                    data = float(match.group(3))
                    text = int(match.group(4))
                    talk = int(match.group(5))
                    
                    # Store the matched data in a dictionary
                    extracted_data.append({
                        'Number': number,
                        'User': user,
                        'Data': data,
                        'Text': text,
                        'Talk': talk
                    })
            self.usage_df = pd.DataFrame(extracted_data)
            self.usage_df.rename(columns={'Number': 'Wireless_number', 'Data': 'Data_Usage','Talk':'Voice Plan Usage','Text':'Messaging Usage'}, inplace=True)
            self.usage_df.drop(columns=['User'], inplace=True)
            flag = len(pages_data) - 1
            str_con = str(flag)
            for page_data in pages_data:
                if f"Page: 1 of {str_con}" in page_data:
                    first_page_data = page_data
                    break
            try:
                self.billing_name = re.search(r"^(.*?)\n", first_page_data).group(1)
                self.Billing_Address = re.search(r"\n(.*?)\n", first_page_data).group(1)
                self.Remidence_Addresss = "PO Box 6463 Carol Stream, IL 60197-646"
            except:
                self.billing_name ='NA'
                self.Billing_Address = 'NA'
                self.Remidence_Addresss = "PO Box 6463 Carol Stream, IL 60197-646"

            total_text = ''.join(pages_data)
            pattern =  r"Group (\d+)\n(\d+) Devices?\nMonthly charges (\w+ \d+ - \w+ \d+)\n1\. (.+) \$([\d.]+)"
            matches = re.findall(pattern, total_text)
            self.plan_price_list = []
            if matches:
                for match in matches:
                    plan_price_dict = {}
                    group_no = match[0]
                    plan = match[3]
                    chrages = match[4]
                    plan_price_dict['Group_Number'] = group_no
                    plan_price_dict['Plans'] = plan
                    plan_price_dict['Monthly_Charges'] = chrages
                    self.plan_price_list.append(plan_price_dict)

            data = ''
            for text in pages_data:
                data += "\n" + text
                match_news = re.search(r"News you can use", data)
                match_usage = re.search(r"Detailed usage", data)

                if match_news or match_usage:
                    break

            self.data = data
        else:
            data = ''
            first_data = ''
            self.plan_price_list = []
            extracted_data.append({
                        'Wireless_number': '',
                        'Data_Usage': '',
                        'Voice Plan Usage': '',
                        'Messaging Usage': ''
                    })
            self.usage_df = pd.DataFrame(extracted_data)
            with pdfplumber.open(self.input_path) as pdf:
                page = pdf.pages[0]
                text = page.extract_text()
                first_data = first_data + "\n" + text
                self.billing_name = re.search(r"^(.*?)\n", first_data).group(1)
                self.Billing_Address = re.search(r"\n(.*?)\n", first_data).group(1)
                self.Remidence_Addresss = "PO Box 6463 Carol Stream, IL 60197-646"
            pdf.close()
            for page_num in range(num_of_pages):
                with pdfplumber.open(self.input_path) as pdf:
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    data = data + "\n" + text
                    self.extract_plans_and_usage(text)

            self.data = data
                    
    def return_no_of_pages(self):
        return self.no_pages

    def extract_plans_and_usage(self, page_text):
            """Extract plan and usage information for each page."""
            # Define patterns to match groups, devices, and usage summaries
            pattern = r"Group (\d+)\n(\d+) Devices?\nMonthly charges (\w+ \d+ - \w+ \d+)\n1\. (.+) \$([\d.]+)"
            pattern2 = r"Group (\d+)\n(\d+) Devices?\nUsage summary"
            
            # Find matches in the current page
            matches = re.findall(pattern, page_text)
            matches2 = re.findall(pattern2, page_text)

            # Process matches for monthly charges
            if matches:
                for match in matches:
                    self.plan_price_list.append({
                        'Group_Number': match[0],
                        'Plans': match[3],
                        'Monthly_Charges': match[4]
                    })

            # Process matches for usage summary
            if matches2:
                for match in matches2:
                    self.plan_price_list.append({
                        'Group_Number': match[0],
                        'Plans': 'NA',
                        'Monthly_Charges': 0
                    })

    def plan_and_price(self):
        return self.plan_price_list,self.usage_df

    def data_manage_part1(self):
        Lines = []
        data_1 = self.data
        lines = data_1.split('\n')
        usage_data = []
        unit_list = []
        num_list = []
        usage_num_list = []
        plan_list = []
        # Define regular expressions to identify wireless numbers, usage categories, and relevant patterns
        phone_number_pattern = re.compile(r'\b(\d{3}\.\d{3}\.\d{4})\b')
        data_used_pattern = re.compile(r'Data Used')
        total_charges_pattern = re.compile(r'Total for')
        dollar_sign_pattern = re.compile(r'\$')
        numeric_value_pattern = re.compile(r'\b(\d{1,3}(,\d{3})*(\.\d+)?)\b(?:\s|$)')
        numeric_value_pattern_contain = re.compile(r'\d')
        talk_used_pattern = re.compile(r'Talk Used')
        text_used_pattern = re.compile(r'Text Used')
        talk_numeric_check = re.compile(r'\b\d+(\.\d+)?\b\s*$')
        plan_pattern = re.compile(r'\b[A-Z]+\d*[A-Z]+\d*[A-Z]+\d*\b')
        # Initialize variables to store the state while parsing
        current_phone_number = None
        found_data_used = False
        found_talk_used = False
        found_text_used = False
        for line in lines:
            phone_match = phone_number_pattern.search(line)
            if phone_match:
                current_phone_number = phone_match.group(1)

            if talk_used_pattern.search(line):
                found_talk_used = True

            if text_used_pattern.search(line):
                found_talk_used = False
                found_text_used = True
            # Look for "Data Used" section
            if data_used_pattern.search(line):
                found_data_used = True
                found_text_used = False

            # If we encounter "Total Charges," stop looking for data usage
            if total_charges_pattern.search(line):
                found_data_used = False

            # Continue only if we are within the "Data Used" section
                
            if found_talk_used:
                if not talk_numeric_check.search(line):
                    continue
                    
                if talk_numeric_check.search(line):
                    shorten_line = line[-8:-1]
                    if not '$' in shorten_line:
                        if not 'Page' in line:
                            if all(x not in line for x in ['Issue Date', 'Account Number', 'Foundation Account', 'Monthly charges', 'Ph[','Ta[','Activity since last bill','5G','4G',]):
    
                                value_match = talk_numeric_check.search(line)
                                value = value_match.group()
                                usage_data.append({current_phone_number:{'Talk Usage':value}})

            if found_text_used:
                if not talk_numeric_check.search(line):
                    continue
                if talk_numeric_check.search(line):
                    shorten_line = line[-8:-1]
                    if not '$' in shorten_line:
                        if not 'Page' in line:
                            if all(x not in line for x in ['Issue Date', 'Account Number', 'Foundation Account', 'Monthly charges', 'Ph[','Ta[','Activity since last bill']):
                                value_match = talk_numeric_check.search(line)
                                value = value_match.group()
                                usage_data.append({current_phone_number:{'Text Usage':value}})

            if found_data_used:
                if '( unlimited GB)' in line:
                        unit = 'GB'
                        unit_list.append({current_phone_number:unit})
                        num_list.append(current_phone_number)
                if dollar_sign_pattern.search(line):
                    continue
                if not numeric_value_pattern_contain.search(line):
                    continue
                if numeric_value_pattern.search(line):
                    if 'KB)' in line:
                        unit = 'KB'
                        unit_list.append({current_phone_number:unit})
                        num_list.append(current_phone_number)
                    if not re.search(r'\b(KB|MB)\b', line):
                        if 'Page' not in line:
                            numeric_match = numeric_value_pattern.search(line)
                            if numeric_match:
                                plan_match = plan_pattern.search(line)
                                if plan_match:
                                    plan = plan_match.group()
                                else:
                                    plan = 'NA'
                                val = numeric_match.group(1)
                                usage_data.append({current_phone_number:{'Data Used':val}})
                                plan_list.append({current_phone_number:{'Plans':plan}})
                                usage_num_list.append(current_phone_number)
        for line in lines:
            match = re.search(
                r'(\d{3}.\d{3}.\d{4}) (.+?|.+? \b\d+\b) (\d+|\d+\,\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-)',
                line)
            if match:
                Lines.append({'Wireless_number': 'NA' if match.group(1) == '-' else match.group(1),
                              'User_name': 'NA' if match.group(2) == '-' else match.group(2),
                              'Page Number': 'NA' if match.group(3) == '-' else match.group(3),
                              'Activity since last bill': 'NA' if match.group(4) == '-' else match.group(4),
                              'Monthly charges Plan': 'NA' if match.group(5) == '-' else match.group(5),
                              'Monthly charges Equipment': 'NA' if match.group(6) == '-' else match.group(6),
                              'Monthly charges Add-ons': 'NA' if match.group(7) == '-' else match.group(7),
                              'Company fees & surcharges': 'NA' if match.group(8) == '-' else match.group(8),
                              'Government fees & taxes': 'NA' if match.group(9) == '-' else match.group(9),
                              'Billing_Name':self.billing_name,
                              'Billing_Address':self.Billing_Address,
                              'Remidence_Addresss':self.Remidence_Addresss,
                              'Total': 'NA' if match.group(10) == '-' else match.group(10)})
            else:
                match = re.search(
                    r'(\d{3}.\d{3}.\d{4}) (.+?|.+? \b\d+\b) (\d+|\d+\,\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-)',
                    line)
                if match:
                    Lines.append({'Wireless_number': 'NA' if match.group(1) == '-' else match.group(1),
                                  'User_name': 'NA' if match.group(2) == '-' else match.group(2),
                                  'Page Number': 'NA' if match.group(3) == '-' else match.group(3),
                                  'Activity since last bill': 'NA' if match.group(4) == '-' else match.group(4),
                                  'Monthly charges': 'NA' if match.group(5) == '-' else match.group(5),
                                  'Company fees & surcharges': 'NA' if match.group(6) == '-' else match.group(6),
                                  'Government fees & taxes': 'NA' if match.group(7) == '-' else match.group(7),
                                  'Billing_Name':self.billing_name,
                                  'Billing_Address':self.Billing_Address,
                                  'Remidence_Addresss':self.Remidence_Addresss,
                                  'Total': 'NA' if match.group(8) == '-' else match.group(8)})
            match = re.search(
                r'(^Group \d+) (\d+|\d+\,\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-)',
                line)
            if match:
                Lines.append({'Wireless_number': 'NA', 'User_name': 'NA' if match.group(1) == '-' else match.group(1),
                              'Page Number': 'NA' if match.group(2) == '-' else match.group(2),
                              'Activity since last bill': 'NA' if match.group(3) == '-' else match.group(3),
                              'Monthly charges Plan': 'NA' if match.group(4) == '-' else match.group(4),
                              'Monthly charges Equipment': 'NA' if match.group(5) == '-' else match.group(5),
                              'Monthly charges Add-ons': 'NA' if match.group(6) == '-' else match.group(6),
                              'Company fees & surcharges': 'NA' if match.group(7) == '-' else match.group(7),
                              'Government fees & taxes': 'NA' if match.group(8) == '-' else match.group(8),
                              'Billing_Name':self.billing_name,
                              'Billing_Address':self.Billing_Address,
                              'Remidence_Addresss':self.Remidence_Addresss,
                              'Total': 'NA' if match.group(9) == '-' else match.group(9)})
            else:
                match = re.search(
                    r'(^Group \d+) (\d+|\d+\,\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\-)',
                    line)
                if match:
                    Lines.append(
                        {'Wireless_number': 'NA', 'User_name': 'NA' if match.group(1) == '-' else match.group(1),
                         'Page Number': 'NA' if match.group(2) == '-' else match.group(2),
                         'Activity since last bill': 'NA' if match.group(3) == '-' else match.group(3),
                         'Monthly charges': 'NA' if match.group(4) == '-' else match.group(4),
                         'Company fees & surcharges': 'NA' if match.group(5) == '-' else match.group(5),
                         'Government fees & taxes': 'NA' if match.group(6) == '-' else match.group(6),
                         'Billing_Name':self.billing_name,
                         'Billing_Address':self.Billing_Address,
                         'Remidence_Addresss':self.Remidence_Addresss,
                         'Total': 'NA' if match.group(7) == '-' else match.group(7)})
        self.Lines_1 = Lines
        usage_dict = {}
        unit_dict = {}
        plan_dict = {}
        # Process the data
        for entry in plan_list:
            for number, plan in entry.items():
                if number not in plan_dict:
                    plan_dict[number] = {'Plans':'NA'}
                for key,value in plan.items():
                    plan_dict[number]['Plans'] = value

        for entry in usage_data:
            for number, usage in entry.items():
                if number not in usage_dict:
                    usage_dict[number] = {'Data Used': 0, 'Text Usage': 0, 'Talk Usage': 0}
                
                for key, value in usage.items():
                    # Remove commas from values and convert to float
                    value = float(value.replace(',', ''))
                    if key == 'Data Used':
                        usage_dict[number]['Data Used'] += value
                    elif key == 'Text Usage':
                        usage_dict[number]['Text Usage'] += value
                    elif key == 'Talk Usage':
                        usage_dict[number]['Talk Usage'] += value

        for entry in unit_list:
            for number, unit in entry.items():
                unit_dict[number] = {'Unit': unit}
        plant_df = pd.DataFrame.from_dict(plan_dict,orient='index').reset_index()
        plant_df.columns = ['Wireless number','Plans']
        all_usage_df = pd.DataFrame.from_dict(usage_dict, orient='index').reset_index()
        all_usage_df.columns = ['Wireless number', 'Data Usage', 'Text Usage', 'Talk Usage']
        units_df = pd.DataFrame.from_dict(unit_dict,orient='index').reset_index()
        units_df.columns = ['Wireless number','Units']
        merged_all_usage_df = pd.merge(all_usage_df,units_df,on='Wireless number',how='left')
        new_merged_df = pd.merge(merged_all_usage_df,plant_df,on='Wireless number',how='left')
        return Lines,new_merged_df

    def geo_member(self):
        unique = set()
        pool = None
        lines = self.data.split('\n')
        for line in lines:
            if line.startswith('Pooling detail'):
                break
            match = re.match(r'^Group (\d+)$', line)
            if match:
                user_name = match.group(1)
                if user_name not in unique:
                    unique.add(user_name)

            if re.compile(
                    r'\b\d{3}\.\d{3}\.\d{4}\b.*\$\d+\.\d{2}\b|\bGroup \d+ \d+ - \$\d+\.\d{2}(- \$\d+\.\d{2})*\b|(?:\bGroup (\d+) (\d+) - \$\d+\.\d{2} - - - - \$\d+\.\d{2}\b|\bGroup (\d+) (\d+) \$\d+\.\d{2} \$\d+\.\d{2} - - \$\d+\.\d{2} \$\d+\.\d{2} \$\d+\.\d{2}\b|Group \d+ \d+ -\$[\d.]+(?: - - - - - -\$[\d.]+)*)').search(
                line):
                items = line.split()
                target_index = None
                if items[0] == 'Group':
                    unique.add(items[1])
        gro_member = []
        uniques = set()
        line_re = re.compile(r'\b\d{3}\.\d{3}\.\d{4}\b.*\$\d+\.\d{2}\b')
        pool = None
        check = 0
        lines = self.data.split('\n')
        for line in lines:
            if check == 1:
                break
            if line.startswith('Pooling detail'):
                pool = 'Data Pool: Mobile Select - Pooled'

            match = re.search(r'Total for Mobile Select - Pooled', line)
            if match:
                check = 1
                break
            match = re.search(r'Group (\d+)', line)
            if match:
                user_name = match.group(1)
                if user_name not in unique:
                    uniques.add(user_name)
            match = re.search(r'Subtotal for Group (\d+)', line)
            if match:
                user_name = None
            if line_re.search(line):
                items = line.split()
                if user_name:
                    gro_member.append({'Group Number': user_name, 'Wireless_number': items[0]})
                if pool:
                    gro_member.append({'Group Number': pool, 'Wireless_number': items[0]})
        return gro_member

    def geo_members(self):
        dataset = []
        gro_members = []
        current_section = None
        lines = self.data.split('\n')
        for i, line in enumerate(lines):
            match = re.search(r"Total for Group (\d+) \$([\d.]+)|Total for Group (\d+) -\$(-?\d+\.\d{2})", line)
            if match:
                current_section = 'Group Plan Cost'
                itemss = line.split()
                gro_name = itemss[-2]
                gro_cost = float(str(itemss[-1]).replace('$', ''))

            match = re.search(r"^Total usage", line)
            if match:
                if dataset:
                    mem_cost = '$' + str(round(gro_cost / float(len(dataset)), 2))
                    for datas in dataset:
                        gro_members.append({'Group Wireless_number': datas, 'Group Number': gro_name,
                                            'Group': mem_cost.replace('$-', '-$')})
                    dataset = []
                current_section = None

            match = re.search(r"(^\d{3}\.\d{3}\.\d{4})\s+([A-Z]+(?:\s+[A-Z]+)*)", line)
            if match:
                if current_section:
                    dataset.append(match.group(1))

        return gro_members

    def data_manage_part2(self):
        result = []
        phone_number = None
        current_section = None
        name = None
        
        data_2 = self.data
        lines = data_2.split('\n')
        note = None
        check = 0
        self.Lines_1,yt= self.data_manage_part1()
        gro_member = self.geo_member()
        gro_members = self.geo_members()
        for i, line in enumerate(lines):
            match = re.search(r"^News you can use", line)
            if match:
                break

            match = re.search(r"^Detailed usage", line)
            if match:
                break

            match = re.search(r"Issue Date: ([A-Za-z]{3} \d{2}, \d{4})", line)
            if match:
                issue_date = match.group(1)

            match = re.search(r"Account Number: (\d+)", line)
            if match:
                account_number = match.group(1)

            match = re.search(r"Invoice: (\d+)X(\d{8})", line)
            if match:
                invoice = match.group(1) + '-' + match.group(2)

            match = re.search(r"Foundation Account: (\d+)", line)
            if match:
                foundation = match.group(1)

            match = re.search(r"Ph\[\[([\d]+o[\d]+)\|\| ne, ([\d]{3}\.[\d]{3}\.[\d]{4})", line)
            if match:
                phone_number = match.group(2)
                name = lines[i + 1]

            match = re.search(r"Ph\[\[([\d]+o[\d]+)\|\|ne, ([\d]{3}\.[\d]{3}\.[\d]{4})", line)
            if match:
                phone_number = match.group(2)
                name = lines[i + 1]

            match = re.search(r"We\[\[([\d]+a[\d]+)\|\| rable, ([\d]{3}\.[\d]{3}\.[\d]{4})", line)
            if match:
                phone_number = match.group(2)
                name = lines[i + 1]

            match = re.search(r"We\[\[([\d]+a[\d]+)\|\|rable, ([\d]{3}\.[\d]{3}\.[\d]{4})", line)
            if match:
                phone_number = match.group(2)
                name = lines[i + 1]

            match = re.search(r"Co\[\[([\d]+n[\d]+)\|\| nected Device, ([\d]{3}\.[\d]{3}\.[\d]{4})", line)
            if match:
                phone_number = match.group(2)
                name = lines[i + 1]

            match = re.search(r"Co\[\[([\d]+n[\d]+)\|\|nected Device, ([\d]{3}\.[\d]{3}\.[\d]{4})", line)
            if match:
                phone_number = match.group(2)
                name = lines[i + 1]

            match = re.search(r"Ta\[\[(\w+)\|\| let, ([\d]{3}\.[\d]{3}\.[\d]{4})", line)
            if match:
                phone_number = match.group(2)
                name = lines[i + 1]

            match = re.search(r"Ta\[\[(\w+)\|\|let, ([\d]{3}\.[\d]{3}\.[\d]{4})", line)
            if match:
                phone_number = match.group(2)
                name = lines[i + 1]

            if re.search(r"Monthly charges", line):
                current_section = 'Monthly charges'
                check = 1
                note = None
            elif re.search(r"Company fees & surcharges", line):
                current_section = 'Company fees & surcharges'
                check = 1
                note = None
            elif re.search(r"Government fees & taxes", line):
                current_section = 'Government fees & taxes'
                note = None
            elif re.search(r"Other Activity", line):
                current_section = 'Other Activity'
                note = 'One-time charge'
            elif re.search(r"(\w+\s\d{2}): (\w+)", line):
                current_section = 'Other Activity'
                note = 'Service change'
            elif re.search(r'Total for \d{3}\.\d{3}\.\d{4}', line):
                current_section = None

            for line_data in self.Lines_1:
                if phone_number:
                    if line_data.get('Wireless_number') == phone_number:
                        try:
                            line_plan = float(
                                str(line_data.get('Monthly charges Plan')).replace('$', '').replace('NA', '0'))
                            if line_plan > 0:
                                status = 'Active'
                            else:
                                status = 'Inactive'
                        except:
                            line_plan = float(str(line_data.get('Monthly charges')).replace('$', '').replace('NA', '0'))
                            if line_plan > 0:
                                status = 'Active'
                            else:
                                status = 'Inactive'

            if current_section == ('Monthly charges' and check == 1) or (
                    current_section == 'Company fees & surcharges' and check == 1):
                check = 0
                if 'status' not in locals():
                    status = 'NA'
                for gro_data in gro_members:
                    if gro_data.get('Group Wireless_number') == phone_number:
                        gro_phone = gro_data.get('Group Wireless_number')
                        data_news1 = gro_data.get('Group Number')
                        mem_cost = gro_data.get('Group')
                        result.append({'Foundation_Account': foundation if foundation else 'NA', 'Account_number': str(account_number),
                                       'Group_Number': data_news1, 'User_name': name, 'Wireless_number': phone_number,
                                       'User_Email': None, 'Status': status, 'Cost_Center': None,
                                       'Account_Charges_and_Credits': None, 'Item_Category': 'Monthly_charges',
                                       'Item_Description': 'Plan_Allocation', 'Charges': mem_cost,'Note': None})
            match = re.search(
                r'(\d+\.) (.*?) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+)',
                line)
            if match:
                if re.search(r'Total for ', line):
                    continue

                if current_section and name:
                    for gro_data1 in gro_member:
                        if gro_data1.get('Wireless_number') == phone_number:
                            gro_phone = gro_data1.get('Wireless_number')
                            data_news1 = gro_data1.get('Group_Number')

                    if gro_phone == phone_number:
                        result.append({'Foundation_Account': foundation if foundation else 'NA', 'Account_number': str(account_number),
                                       'Group_Number': data_news1, 'User_name': name, 'Wireless_number': phone_number,
                                       'User_Email': None, 'Status': status if 'status' in locals() else 'NA', 'Cost_Center': None,
                                       'Account_Charges_and_Credits': None, 'Item_Category': current_section,
                                       'Item_Description': match.group(2), 'Charges': match.group(3),
                                       'Note': note if note != None else None})
                    else:
                        result.append(
                            {'Foundation_Account': foundation if foundation else 'NA', 'Account_number': str(account_number),
                             'Group_Number': None,
                             'User_name': name, 'Wireless_number': phone_number, 'User_Email': None, 'Status': status,
                             'Cost_Center': None, 'Account_Charges_and_Credits': None, 'Item_Category': current_section,
                             'Item_Description': match.group(2), 'Charges': match.group(3),'Note': note if note != None else None})
        return result
    
    def to_csv(self, List_data):
        df = pd.DataFrame(List_data)
        return df

def get_first_page_data(uploaded_file):
    obj = first_page_extractor(uploaded_file)
    first_dict = obj.first_page_data_func()
    acc = obj.get_acc_info()
    incv = obj.get_invoice_number_info()
    bill_date = obj.get_bill_date_info()
    fa = obj.get_foundation_account()
    return first_dict,acc,incv,bill_date,fa

def process_all(uploaded_file):
    fs,acc,incv,bill_date,fa = get_first_page_data(uploaded_file)
    data_list = Att(uploaded_file)
    no_of_pages = data_list.return_no_of_pages()
    x,usage_df = data_list.plan_and_price()
    plan_price_df = data_list.to_csv(x)
    z,yt = data_list.data_manage_part1()
    unique_df = data_list.to_csv(z)
    y = data_list.data_manage_part2()
    intital_df = data_list.to_csv(y)
    final_df = pd.merge(intital_df,plan_price_df,on='Group_Number',how='inner')
    if no_of_pages <= 100:
        new_df = pd.merge(unique_df,usage_df,on='Wireless_number',how='left')
        unique_df = new_df
    else:
        unique_df['Account_number'] = acc
        unique_df['foundation_account'] = fa
        yt.rename(columns={'Text Usage':'Messaging Usage','Talk Usage':'Voice_Plan_Usage ','Wireless number':'Wireless_number'},inplace=True)
        new_merged_summary_df = pd.merge(unique_df,yt,on='Wireless_number',how='left')
        def insert_mb(row):
            data_usage = row['Data Usage']
            unit = row['Units']
            
            # Check if 'data_usage' has a value and 'Units' is empty or NaN
            if pd.notna(data_usage) and (pd.isna(unit) or unit == ''):
                row['Units'] = 'MB'  # Update 'Units' to 'MB'
            
            return row['Units']  # Return the updated or original 'Units' value

        new_merged_summary_df['Units'] = new_merged_summary_df.apply(insert_mb, axis=1)

        def convert_to_gb(row):
            usage = row['Data Usage']
            unit = row['Units']
            
            if pd.isna(usage) or usage == "":  # Check if empty or NaN
                return ""
            
            try:
                usage = float(usage)  # Convert usage to float if not already
            except ValueError:
                return ""  # Return empty for invalid entries
            
            if unit == 'KB':
                return round(usage / 1048576, 2)  # Convert KB to GB and round to 6 decimal places
            elif unit == 'MB':  # Assuming MB if no unit is mentioned
                return round(usage / 1024, 2)  # Convert MB to GB and round
            elif unit == 'GB':
                return round(usage, 3)  # Keep GB as is, rounded to 6 decimal places
            else:
                return ""  # 
        new_merged_summary_df['Data Usage'] = new_merged_summary_df.apply(convert_to_gb, axis=1)
        new_merged_summary_df.drop('Units', axis=1, inplace=True)
        def insert_zeros(row):
            data_usage = row['Data Usage']
            
            # Check if 'data_usage' has a value and 'Units' is empty or NaN
            if pd.isna(data_usage) or data_usage == '':
                row['Data Usage'] = 0  # Update 'Units' to 'MB'
            
            return row['Data Usage']  # Return the updated or original 'Units' value
        new_df = new_merged_summary_df
        new_df['Data Usage'] = new_df.apply(insert_zeros,axis=1)
        unique_df = new_df
        final_df = new_df
    return unique_df,final_df,usage_df,intital_df

